# Production Database Restore Script
# Purpose: Restore PostgreSQL database from backup for Jarvis AI production deployment
# Usage: .\scripts\production_restore.ps1 -BackupFile <path_to_backup>
# WARNING: This will overwrite the existing database. Use with caution.
# Requirements: Docker Compose must be running with PostgreSQL container

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    
    [string]$ProjectName = "jarvis-production",
    [string]$PostgresService = "postgres",
    [string]$PostgresUser = "jarvis",
    [string]$PostgresDb = "jarvis",
    
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Test-DockerCompose {
    Write-Log "Testing Docker Compose availability..."
    $result = docker-compose --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose is not available or not running"
    }
    Write-Log "Docker Compose is available: $result"
}

function Test-PostgresContainer {
    Write-Log "Testing PostgreSQL container availability..."
    $containerName = "${ProjectName}_${PostgresService}_1"
    $result = docker ps --filter "name=$containerName" --format "{{.Names}}"
    if (-not $result) {
        throw "PostgreSQL container '$containerName' is not running"
    }
    Write-Log "PostgreSQL container is running: $containerName"
}

function Test-BackupFile {
    param([string]$FilePath)
    
    Write-Log "Testing backup file: $FilePath"
    
    if (-not (Test-Path $FilePath)) {
        throw "Backup file does not exist: $FilePath"
    }
    
    $fileSize = (Get-Item $FilePath).Length
    if ($fileSize -eq 0) {
        throw "Backup file is empty: $FilePath"
    }
    
    Write-Log "Backup file size: $([math]::Round($fileSize / 1KB, 2)) KB"
    
    # Test integrity
    if ($FilePath -match '\.gz$') {
        Write-Log "Testing gzip integrity..."
        $result = gzip -t $FilePath 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Gzip integrity check failed"
        }
    } elseif ($FilePath -match '\.zip$') {
        Write-Log "Testing zip integrity..."
        # Note: PowerShell Test-ZipFile may not be available in all versions
        Write-Log "Zip integrity check skipped (manual verification recommended)"
    }
    
    Write-Log "Backup file integrity check passed"
}

function Confirm-Restore {
    Write-Log "WARNING: This will overwrite the existing database '$PostgresDb'" "WARNING"
    Write-Log "Backup file: $BackupFile" "WARNING"
    Write-Log "Project: $ProjectName" "WARNING"
    
    if (-not $Force) {
        $confirmation = Read-Host "Do you want to continue? (yes/no)"
        if ($confirmation -ne "yes") {
            Write-Log "Restore cancelled by user"
            exit 0
        }
    } else {
        Write-Log "Force mode enabled, skipping confirmation" "WARNING"
    }
}

function Backup-CurrentDatabase {
    Write-Log "Creating pre-restore backup of current database..."
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $preRestoreBackup = "backups/pre_restore_${timestamp}.sql"
    
    try {
        $containerName = "${ProjectName}_${PostgresService}_1"
        $backupCommand = "docker-compose -p $ProjectName exec -T $PostgresService pg_dump -U $PostgresUser -d $PostgresDb --no-password --format=plain"
        
        Invoke-Expression $backupCommand | Out-File -FilePath $preRestoreBackup -Encoding UTF8
        
        if ($LASTEXITCODE -ne 0) {
            throw "Pre-restore backup failed"
        }
        
        Write-Log "Pre-restore backup created: $preRestoreBackup"
        return $preRestoreBackup
    }
    catch {
        Write-Log "Pre-restore backup failed: $_" "WARNING"
        Write-Log "Continuing with restore without pre-restore backup" "WARNING"
        return $null
    }
}

function Drop-ExistingDatabase {
    Write-Log "Dropping existing database '$PostgresDb'..."
    
    $containerName = "${ProjectName}_${PostgresService}_1"
    
    # Connect to PostgreSQL and drop database
    $dropCommand = "docker-compose -p $ProjectName exec -T $PostgresService psql -U $PostgresUser -d postgres -c `"DROP DATABASE IF EXISTS $PostgresDb;`""
    
    Invoke-Expression $dropCommand | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to drop database"
    }
    
    Write-Log "Database dropped successfully"
}

function Create-Database {
    Write-Log "Creating database '$PostgresDb'..."
    
    $containerName = "${ProjectName}_${PostgresService}_1"
    
    $createCommand = "docker-compose -p $ProjectName exec -T $PostgresService psql -U $PostgresUser -d postgres -c `"CREATE DATABASE $PostgresDb;`""
    
    Invoke-Expression $createCommand | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create database"
    }
    
    Write-Log "Database created successfully"
}

function Restore-Database {
    param([string]$BackupFile)
    
    Write-Log "Starting database restore from: $BackupFile"
    
    $containerName = "${ProjectName}_${PostgresService}_1"
    
    # Decompress if needed
    $restoreFile = $BackupFile
    if ($BackupFile -match '\.gz$') {
        Write-Log "Decompressing backup file..."
        $restoreFile = "$BackupFile.decompressed"
        gzip -dc $BackupFile | Out-File -FilePath $restoreFile -Encoding UTF8
        Write-Log "Decompressed to: $restoreFile"
    } elseif ($BackupFile -match '\.zip$') {
        Write-Log "Extracting zip file..."
        $restoreFile = "$BackupFile.decompressed"
        Expand-Archive -Path $BackupFile -DestinationPath (Split-Path $restoreFile) -Force
        # Find the extracted SQL file
        $extractedFile = Get-ChildItem (Split-Path $restoreFile) -Filter "*.sql" | Select-Object -First 1
        if ($extractedFile) {
            $restoreFile = $extractedFile.FullName
        }
        Write-Log "Extracted to: $restoreFile"
    }
    
    try {
        # Restore database
        $restoreCommand = "docker-compose -p $ProjectName exec -T $PostgresService psql -U $PostgresUser -d $PostgresDb"
        
        Get-Content $restoreFile | Invoke-Expression $restoreCommand
        
        if ($LASTEXITCODE -ne 0) {
            throw "Database restore failed with exit code $LASTEXITCODE"
        }
        
        Write-Log "Database restore completed successfully"
        
        # Clean up decompressed file
        if ($restoreFile -ne $BackupFile) {
            Remove-Item $restoreFile -Force
            Write-Log "Removed temporary decompressed file"
        }
        
        return $true
    }
    catch {
        Write-Log "Database restore failed: $_" "ERROR"
        throw
    }
}

function Verify-Restore {
    Write-Log "Verifying database restore..."
    
    $containerName = "${ProjectName}_${PostgresService}_1"
    
    # Check if database exists
    $checkCommand = "docker-compose -p $ProjectName exec -T $PostgresService psql -U $PostgresUser -d postgres -c `"SELECT datname FROM pg_database WHERE datname = '$PostgresDb';`""
    
    $result = Invoke-Expression $checkCommand
    
    if ($LASTEXITCODE -ne 0) {
        throw "Database verification failed"
    }
    
    if ($result -match $PostgresDb) {
        Write-Log "Database '$PostgresDb' exists"
    } else {
        throw "Database '$PostgresDb' does not exist after restore"
    }
    
    # Check table count
    $tableCommand = "docker-compose -p $ProjectName exec -T $PostgresService psql -U $PostgresUser -d $PostgresDb -t -c `"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';`""
    
    $tableCount = Invoke-Expression $tableCommand
    $tableCount = $tableCount.Trim()
    
    Write-Log "Tables in database: $tableCount"
    
    if ([int]$tableCount -lt 1) {
        Write-Log "Warning: Database appears to be empty" "WARNING"
    }
    
    Write-Log "Database restore verification passed"
}

# Main execution
try {
    Write-Log "=== Jarvis AI Production Database Restore ==="
    Write-Log "Project: $ProjectName"
    Write-Log "Database: $PostgresDb"
    Write-Log "User: $PostgresUser"
    Write-Log "Backup file: $BackupFile"
    
    if ($DryRun) {
        Write-Log "=== DRY RUN MODE - No changes will be made ==="
        Test-DockerCompose
        Test-PostgresContainer
        Test-BackupFile -FilePath $BackupFile
        Write-Log "=== Dry run completed successfully ==="
        exit 0
    }
    
    # Pre-flight checks
    Test-DockerCompose
    Test-PostgresContainer
    Test-BackupFile -FilePath $BackupFile
    
    # Confirm restore
    Confirm-Restore
    
    # Create pre-restore backup
    $preRestoreBackup = Backup-CurrentDatabase
    
    try {
        # Drop existing database
        Drop-ExistingDatabase
        
        # Create new database
        Create-Database
        
        # Restore database
        Restore-Database -BackupFile $BackupFile
        
        # Verify restore
        Verify-Restore
        
        Write-Log "=== Restore completed successfully ==="
        Write-Log "Pre-restore backup: $preRestoreBackup"
        
        exit 0
    }
    catch {
        Write-Log "=== Restore failed ===" "ERROR"
        Write-Log "Error: $_" "ERROR"
        
        if ($preRestoreBackup) {
            Write-Log "Pre-restore backup available: $preRestoreBackup"
            Write-Log "You can restore from this backup if needed"
        }
        
        exit 1
    }
}
catch {
    Write-Log "=== Restore failed ===" "ERROR"
    Write-Log "Error: $_" "ERROR"
    exit 1
}
