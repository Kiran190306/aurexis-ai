# Production Database Backup Script
# Purpose: Backup PostgreSQL database for Jarvis AI production deployment
# Usage: .\scripts\production_backup.ps1
# Requirements: Docker Compose must be running with PostgreSQL container

[CmdletBinding()]
param(
    [string]$ProjectName = "jarvis-production",
    [string]$PostgresService = "postgres",
    [string]$PostgresUser = "jarvis",
    [string]$PostgresDb = "jarvis",
    [string]$BackupDir = "backups",
    [switch]$Compress = $true
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

function New-BackupDirectory {
    Write-Log "Creating backup directory..."
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        Write-Log "Created backup directory: $BackupDir"
    } else {
        Write-Log "Backup directory already exists: $BackupDir"
    }
}

function Get-BackupFilename {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $filename = "jarvis_backup_${timestamp}.sql"
    return Join-Path $BackupDir $filename
}

function Invoke-DatabaseBackup {
    param([string]$BackupFile)
    
    Write-Log "Starting database backup to: $BackupFile"
    
    $containerName = "${ProjectName}_${PostgresService}_1"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Execute pg_dump inside the PostgreSQL container
    $backupCommand = "docker-compose -p $ProjectName exec -T $PostgresService pg_dump -U $PostgresUser -d $PostgresDb --no-password --format=plain --verbose"
    
    try {
        # Run backup and redirect to file
        Invoke-Expression $backupCommand | Out-File -FilePath $BackupFile -Encoding UTF8
        
        if ($LASTEXITCODE -ne 0) {
            throw "Database backup failed with exit code $LASTEXITCODE"
        }
        
        # Verify backup file exists and has content
        if (-not (Test-Path $BackupFile)) {
            throw "Backup file was not created"
        }
        
        $fileSize = (Get-Item $BackupFile).Length
        if ($fileSize -eq 0) {
            throw "Backup file is empty"
        }
        
        Write-Log "Database backup completed successfully"
        Write-Log "Backup file size: $([math]::Round($fileSize / 1KB, 2)) KB"
        
        return $true
    }
    catch {
        Write-Log "Database backup failed: $_" "ERROR"
        throw
    }
}

function Compress-BackupFile {
    param([string]$BackupFile)
    
    Write-Log "Compressing backup file..."
    
    $compressedFile = "$BackupFile.gz"
    
    try {
        # Compress using gzip (if available) or PowerShell Compress-Archive
        if (Get-Command gzip -ErrorAction SilentlyContinue) {
            gzip -c $BackupFile | Out-File -FilePath $compressedFile -Encoding Byte
        } else {
            Compress-Archive -Path $BackupFile -DestinationPath "$compressedFile.zip" -Force
            $compressedFile = "$compressedFile.zip"
        }
        
        $originalSize = (Get-Item $BackupFile).Length
        $compressedSize = (Get-Item $compressedFile).Length
        $compressionRatio = [math]::Round((1 - ($compressedSize / $originalSize)) * 100, 2)
        
        Write-Log "Backup compressed successfully"
        Write-Log "Original size: $([math]::Round($originalSize / 1KB, 2)) KB"
        Write-Log "Compressed size: $([math]::Round($compressedSize / 1KB, 2)) KB"
        Write-Log "Compression ratio: $compressionRatio%"
        
        # Remove uncompressed backup
        Remove-Item $BackupFile -Force
        Write-Log "Removed uncompressed backup file"
        
        return $compressedFile
    }
    catch {
        Write-Log "Backup compression failed: $_" "ERROR"
        Write-Log "Keeping uncompressed backup file"
        return $BackupFile
    }
}

function Test-BackupIntegrity {
    param([string]$BackupFile)
    
    Write-Log "Testing backup integrity..."
    
    try {
        # Check if file is gzip compressed
        if ($BackupFile -match '\.gz$') {
            # Test gzip integrity
            $result = gzip -t $BackupFile 2>&1
            if ($LASTEXITCODE -ne 0) {
                throw "Gzip integrity check failed"
            }
        } elseif ($BackupFile -match '\.zip$') {
            # Test zip integrity
            $result = Test-ZipFile -Path $BackupFile
            if (-not $result) {
                throw "Zip integrity check failed"
            }
        } else {
            # For plain SQL files, check if it's valid SQL
            $content = Get-Content $BackupFile -Raw
            if (-not $content -match "PostgreSQL database dump") {
                throw "Backup file does not appear to be a valid PostgreSQL dump"
            }
        }
        
        Write-Log "Backup integrity check passed"
        return $true
    }
    catch {
        Write-Log "Backup integrity check failed: $_" "ERROR"
        throw
    }
}

function Get-BackupMetadata {
    param([string]$BackupFile)
    
    Write-Log "Generating backup metadata..."
    
    $metadata = @{
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        filename = Split-Path $BackupFile -Leaf
        size = (Get-Item $BackupFile).Length
        size_human = "{0:N2} KB" -f ((Get-Item $BackupFile).Length / 1KB)
        postgres_version = ""
        database_name = $PostgresDb
        project_name = $ProjectName
    }
    
    # Extract PostgreSQL version from backup file
    try {
        if ($BackupFile -match '\.gz$') {
            $content = gzip -dc $BackupFile | Select-String "PostgreSQL database dump" -Context 0,2
        } else {
            $content = Select-String -Path $BackupFile -Pattern "PostgreSQL database dump" -Context 0,2
        }
        
        if ($content) {
            $versionLine = $content.Line
            if ($versionLine -match "PostgreSQL (\d+\.\d+)") {
                $metadata.postgres_version = $matches[1]
            }
        }
    }
    catch {
        Write-Log "Could not extract PostgreSQL version from backup" "WARNING"
    }
    
    $metadataFile = $BackupFile + ".metadata.json"
    $metadata | ConvertTo-Json | Out-File -FilePath $metadataFile -Encoding UTF8
    
    Write-Log "Backup metadata saved to: $metadataFile"
    return $metadataFile
}

# Main execution
try {
    Write-Log "=== Jarvis AI Production Database Backup ==="
    Write-Log "Project: $ProjectName"
    Write-Log "Database: $PostgresDb"
    Write-Log "User: $PostgresUser"
    
    # Pre-flight checks
    Test-DockerCompose
    Test-PostgresContainer
    New-BackupDirectory
    
    # Generate backup filename
    $backupFile = Get-BackupFilename
    Write-Log "Backup file: $backupFile"
    
    # Execute backup
    Invoke-DatabaseBackup -BackupFile $backupFile
    
    # Compress if requested
    if ($Compress) {
        $backupFile = Compress-BackupFile -BackupFile $backupFile
    }
    
    # Test integrity
    Test-BackupIntegrity -BackupFile $backupFile
    
    # Generate metadata
    Get-BackupMetadata -BackupFile $backupFile
    
    Write-Log "=== Backup completed successfully ==="
    Write-Log "Backup file: $backupFile"
    
    exit 0
}
catch {
    Write-Log "=== Backup failed ===" "ERROR"
    Write-Log "Error: $_" "ERROR"
    exit 1
}
