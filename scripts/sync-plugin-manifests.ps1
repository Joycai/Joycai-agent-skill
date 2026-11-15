param([switch]$Check)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$market = Get-Content -LiteralPath "$root/.claude-plugin/marketplace.json" -Raw | ConvertFrom-Json
$entries = @()
$outputs = @{}
foreach ($entry in $market.plugins) {
    $pluginRoot = Join-Path $root $entry.source
    $manifest = Get-Content -LiteralPath "$pluginRoot/.claude-plugin/plugin.json" -Raw | ConvertFrom-Json
    if ($manifest.name -ne $entry.name -or $manifest.version -ne $entry.version) {
        throw "Claude marketplace and manifest disagree: $($entry.name)"
    }
    if (-not (Get-ChildItem -LiteralPath "$pluginRoot/skills" -Filter SKILL.md -Recurse)) {
        throw "No skills found: $($entry.name)"
    }
    $codex = [ordered]@{
        name = $manifest.name
        version = $manifest.version
        description = $manifest.description
        author = $manifest.author
        keywords = $manifest.keywords
        skills = './skills'
    }
    $outputs["$pluginRoot/.codex-plugin/plugin.json"] = $codex
    $entries += [ordered]@{
        name = $entry.name
        source = [ordered]@{ source = 'local'; path = $entry.source }
        policy = [ordered]@{ installation = 'AVAILABLE'; authentication = 'ON_INSTALL' }
        category = 'Productivity'
    }
}
$outputs["$root/.agents/plugins/marketplace.json"] = [ordered]@{
    name = $market.name
    interface = [ordered]@{ displayName = 'Joycai Agent Skills' }
    plugins = $entries
}
foreach ($path in $outputs.Keys) {
    $json = ($outputs[$path] | ConvertTo-Json -Depth 20) + "`n"
    if ($Check) {
        if (-not (Test-Path -LiteralPath $path)) { throw "Missing generated manifest: $path" }
        $actual = [IO.File]::ReadAllText($path).Replace("`r`n", "`n").TrimEnd()
        if ($actual -ne $json.Replace("`r`n", "`n").TrimEnd()) { throw "Manifest out of sync: $path" }
    } else {
        [IO.Directory]::CreateDirectory((Split-Path $path -Parent)) | Out-Null
        [IO.File]::WriteAllText($path, $json, [Text.UTF8Encoding]::new($false))
    }
}
Write-Output "OK: $($entries.Count) plugins; Claude/Codex metadata and skill directories checked."
