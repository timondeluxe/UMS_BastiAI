# 🐍 Virtual Environment Auto-Activation

Dieses Projekt ist so konfiguriert, dass das virtuelle Environment automatisch aktiviert wird, wenn Sie den Ordner in VS Code oder Cursor öffnen.

## ✅ Was wurde eingerichtet:

### 1. VS Code/Cursor Integration (`.vscode/settings.json`)
- **Automatische Python-Interpreter-Auswahl**: Verwendet `./venv/Scripts/python.exe`
- **Terminal-Activation**: Aktiviert das venv automatisch in neuen Terminals
- **PowerShell-Integration**: Spezielle PowerShell-Konfiguration für venv-Activation

### 2. Manuelle Activation
- **`.\venv\Scripts\Activate.ps1`**: PowerShell-Script für manuelle Activation

## 🚀 Wie es funktioniert:

### Automatisch (VS Code/Cursor):
1. Öffnen Sie den Ordner in VS Code oder Cursor
2. Das virtuelle Environment wird automatisch aktiviert
3. Neue Terminals verwenden automatisch das venv

## 🔧 Troubleshooting:

### Falls die Auto-Activation nicht funktioniert:
1. **Execution Policy prüfen**:
   ```powershell
   Get-ExecutionPolicy
   # Sollte "RemoteSigned" oder "Unrestricted" sein
   ```

2. **Execution Policy setzen** (falls nötig):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Manuell aktivieren**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

### Falls das venv nicht existiert:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📁 Dateien im Detail:

- **`.vscode/settings.json`**: VS Code/Cursor Konfiguration
- **`activate.ps1`**: PowerShell Activation-Script
- **`activate.bat`**: Command Prompt Activation-Script
- **`.vscode/activate_env.ps1`**: Erweiterte Activation mit Logging

## 🎯 Ergebnis:

Wenn Sie den Ordner öffnen, sollten Sie sehen:
```
🐍 Activating virtual environment...
✅ Virtual environment activated!
📁 Working directory: C:\Users\yawei\Google Drive\Woxow\ums__chunking
🐍 Python version: Python 3.x.x
(venv) PS C:\Users\yawei\Google Drive\Woxow\ums__chunking>
```

Das `(venv)` am Anfang der Prompt zeigt, dass das virtuelle Environment aktiv ist! 🎉
