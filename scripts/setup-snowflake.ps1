param(
    [switch]$SkipStreamlitDeployment,
    [switch]$AppOnly
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$snowCli = Join-Path $repoRoot ".venv\Scripts\snow.exe"
$snowflakeHome = Join-Path $repoRoot ".snowflake"
$statusFile = Join-Path $snowflakeHome "deployment-status.txt"
$logFile = Join-Path $snowflakeHome "deployment-output.log"
$credentialFile = Join-Path $snowflakeHome "shadowtrace-credential.clixml"

Set-Location -LiteralPath $repoRoot
$env:SNOWFLAKE_HOME = $snowflakeHome

if (-not (Test-Path -LiteralPath $snowCli)) {
    throw "Snowflake CLI is missing from the project virtual environment."
}

New-Item -ItemType Directory -Path $snowflakeHome -Force | Out-Null
Set-Content -LiteralPath $statusFile -Value "WAITING_FOR_PASSWORD"
Set-Content -LiteralPath $logFile -Value "ShadowTraceAI Snowflake deployment"

function Invoke-SnowCommand {
    param([Parameter(Mandatory)][string[]]$Arguments)

    # Snowflake CLI emits benign configuration warnings on stderr. Capture them
    # in the diagnostic log without allowing PowerShell 5 to treat stderr as a
    # terminating error; the native process exit code remains authoritative.
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $snowCli @Arguments 2>&1 | Tee-Object -FilePath $logFile -Append
        $snowExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorPreference
    }

    if ($snowExitCode -ne 0) {
        throw "Snowflake CLI failed with exit code $snowExitCode."
    }
}

$credentialWasStored = Test-Path -LiteralPath $credentialFile
if ($credentialWasStored) {
    $storedCredential = Import-Clixml -LiteralPath $credentialFile
    if ($storedCredential -isnot [System.Management.Automation.PSCredential]) {
        throw "The stored Snowflake credential is invalid. Delete $credentialFile and retry."
    }
    $securePassword = $storedCredential.Password
    Write-Host "Using the Windows-encrypted Snowflake credential for Asthakashyap."
}
else {
    $securePassword = Read-Host "Enter the Snowflake password for Asthakashyap" -AsSecureString
}
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    $env:SNOWFLAKE_CONNECTIONS_SHADOWTRACE_PASSWORD = $plainPassword
    $plainPassword = $null

    Set-Content -LiteralPath $statusFile -Value "TESTING_CONNECTION"
    Invoke-SnowCommand -Arguments @("connection", "test", "-c", "shadowtrace")
    Invoke-SnowCommand -Arguments @(
        "sql", "-c", "shadowtrace", "-q",
        "SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_VERSION()"
    )

    if (-not $credentialWasStored) {
        $credential = [System.Management.Automation.PSCredential]::new("Asthakashyap", $securePassword)
        $credential | Export-Clixml -LiteralPath $credentialFile
        Write-Host "Saved an encrypted Windows-user credential at $credentialFile."
    }

    Set-Content -LiteralPath $statusFile -Value "CONNECTED_AWAITING_CONFIRMATION"
    $confirmationMessage = if ($AppOnly) {
        "Connection succeeded. Publish the updated ShadowTraceAI Streamlit interface? (y/N)"
    }
    else {
        "Connection succeeded. Create SHADOWTRACE_AI, upload synthetic data, run tests, and deploy the app? (y/N)"
    }
    $answer = Read-Host $confirmationMessage
    if ($answer -notin @("y", "Y", "yes", "YES", "Yes")) {
        Set-Content -LiteralPath $statusFile -Value "CONNECTED_NOT_DEPLOYED"
        Write-Host "Connection verified. Deployment was not started."
        return
    }

    Set-Content -LiteralPath $statusFile -Value "DEPLOYING"
    if ($AppOnly) {
        Write-Host "Publishing the updated Snowflake-native Streamlit app ..."
        Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "sql/07_deploy_streamlit.sql")
        Set-Content -LiteralPath $statusFile -Value "COMPLETE"
        Write-Host ""
        Write-Host "ShadowTraceAI interface published successfully." -ForegroundColor Green
        Write-Host "Open SHADOWTRACE_AI.AML.SHADOWTRACEAI_APP in Snowsight."
        return
    }

    $buildScripts = @(
        "sql/01_schema.sql",
        "sql/02_load_seed_data.sql",
        "sql/03_typology_views.sql",
        "sql/04_risk_scoring.sql",
        "sql/05_case_brief.sql",
        "sql/06_decisions_audit.sql",
        "sql/08_investigation_copilot.sql",
        "sql/09_multi_agent_orchestration.sql",
        "sql/10_cortex_agent.sql",
        "sql/11_transaction_pipeline.sql"
    )

    foreach ($script in $buildScripts) {
        Write-Host "Running $script ..."
        Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", $script)
    }

    Write-Host "Running risk-logic acceptance tests ..."
    Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "tests/test_risk_logic.sql")
    Write-Host "Running Investigation Copilot persistence test ..."
    Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "tests/test_copilot.sql")
    Write-Host "Running multi-agent orchestration test ..."
    Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "tests/test_multi_agent.sql")
    Write-Host "Running first-class Cortex Agent test ..."
    Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "tests/test_cortex_agent.sql")
    Write-Host "Running new-transaction pipeline test ..."
    Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "tests/test_new_transaction_pipeline.sql")

    if (-not $SkipStreamlitDeployment) {
        Write-Host "Deploying the Snowflake-native Streamlit app ..."
        Invoke-SnowCommand -Arguments @("sql", "-c", "shadowtrace", "-f", "sql/07_deploy_streamlit.sql")
    }

    Set-Content -LiteralPath $statusFile -Value "COMPLETE"
    Write-Host ""
    Write-Host "ShadowTraceAI deployment completed successfully." -ForegroundColor Green
    Write-Host "Open SHADOWTRACE_AI.AML.SHADOWTRACEAI_APP in Snowsight."
}
catch {
    Set-Content -LiteralPath $statusFile -Value "FAILED"
    $_ | Out-String | Add-Content -LiteralPath $logFile
    Write-Host ""
    Write-Host "Setup failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Diagnostic output: $logFile"
}
finally {
    Remove-Item Env:SNOWFLAKE_CONNECTIONS_SHADOWTRACE_PASSWORD -ErrorAction SilentlyContinue
    if ($passwordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    }
    $securePassword = $null
    Read-Host "Press Enter to close this window"
}
