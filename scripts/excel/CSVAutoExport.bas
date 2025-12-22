Attribute VB_Name = "CSVAutoExport"
'===============================================================================
' CSV Auto-Export Module
'===============================================================================
' Automatically exports all visible worksheets to UTF-8 CSV files when the
' workbook is saved. Designed for the Residency Scheduler import system.
'
' Features:
'   - Auto-export on workbook save
'   - UTF-8 encoding for international character support
'   - Sanitized filenames (removes invalid characters)
'   - Skips hidden sheets
'   - Manual trigger via Ctrl+Shift+E
'
' Installation:
'   1. Open VBA Editor (Alt+F11)
'   2. File > Import File > select this .bas file
'   3. Copy ThisWorkbook_BeforeSave code to ThisWorkbook module
'
' Naming Convention:
'   {WorkbookName}_{SheetName}.csv
'   Example: Schedule_Block10.xlsx with sheet "Residents" -> Schedule_Block10_Residents.csv
'
' Author: Claude Code Assistant
' Version: 1.0.0
' Date: 2024
'===============================================================================

Option Explicit

' Configuration constants
Private Const CSV_DELIMITER As String = ","
Private Const SHOW_COMPLETION_MESSAGE As Boolean = True
Private Const SKIP_HIDDEN_SHEETS As Boolean = True

'===============================================================================
' Public API
'===============================================================================

'''
' Exports all visible worksheets to CSV files in the same directory as the workbook.
' This is the main entry point - call this manually or from Workbook_BeforeSave.
'
' @param ShowMessage If True, displays a message box on completion
' @return Integer Number of files exported
'''
Public Function ExportAllSheetsToCSV(Optional ShowMessage As Boolean = True) As Integer
    Dim ws As Worksheet
    Dim exportCount As Integer
    Dim workbookPath As String
    Dim workbookBaseName As String
    Dim csvPath As String
    Dim sanitizedSheetName As String

    ' Ensure workbook is saved (has a path)
    If Len(ThisWorkbook.Path) = 0 Then
        If ShowMessage Then
            MsgBox "Please save the workbook first before exporting to CSV.", _
                   vbExclamation, "CSV Export"
        End If
        ExportAllSheetsToCSV = 0
        Exit Function
    End If

    workbookPath = ThisWorkbook.Path
    workbookBaseName = GetWorkbookBaseName()
    exportCount = 0

    ' Export each visible worksheet
    For Each ws In ThisWorkbook.Worksheets
        ' Skip hidden sheets if configured
        If SKIP_HIDDEN_SHEETS And ws.Visible <> xlSheetVisible Then
            GoTo NextSheet
        End If

        ' Sanitize sheet name for filename
        sanitizedSheetName = SanitizeFileName(ws.Name)

        ' Build CSV file path
        csvPath = workbookPath & Application.PathSeparator & _
                  workbookBaseName & "_" & sanitizedSheetName & ".csv"

        ' Export the worksheet
        If ExportWorksheetToCSV(ws, csvPath) Then
            exportCount = exportCount + 1
        End If

NextSheet:
    Next ws

    ' Show completion message if requested
    If ShowMessage And SHOW_COMPLETION_MESSAGE Then
        MsgBox "Exported " & exportCount & " worksheet(s) to CSV files." & vbCrLf & _
               "Location: " & workbookPath, _
               vbInformation, "CSV Export Complete"
    End If

    ExportAllSheetsToCSV = exportCount
End Function

'''
' Manual trigger for CSV export (can be assigned to Ctrl+Shift+E).
' Call this from a keyboard shortcut or ribbon button.
'''
Public Sub ManualExportToCSV()
    Call ExportAllSheetsToCSV(True)
End Sub

'''
' Assigns the keyboard shortcut Ctrl+Shift+E to the export function.
' Call this once to set up the shortcut, or add to Workbook_Open.
'''
Public Sub AssignKeyboardShortcut()
    Application.OnKey "^+e", "ManualExportToCSV"
    MsgBox "Keyboard shortcut Ctrl+Shift+E assigned to CSV Export.", _
           vbInformation, "Shortcut Assigned"
End Sub

'''
' Removes the keyboard shortcut assignment.
'''
Public Sub RemoveKeyboardShortcut()
    Application.OnKey "^+e"
End Sub

'===============================================================================
' Private Helper Functions
'===============================================================================

'''
' Exports a single worksheet to a UTF-8 encoded CSV file.
'
' @param ws The worksheet to export
' @param filePath Full path for the output CSV file
' @return Boolean True if export succeeded
'''
Private Function ExportWorksheetToCSV(ws As Worksheet, filePath As String) As Boolean
    On Error GoTo ErrorHandler

    Dim stream As Object
    Dim csvContent As String
    Dim row As Long
    Dim col As Long
    Dim lastRow As Long
    Dim lastCol As Long
    Dim rowData As String
    Dim cellValue As String
    Dim usedRange As Range

    ' Get used range
    Set usedRange = ws.UsedRange

    ' Handle empty sheets
    If usedRange Is Nothing Then
        ExportWorksheetToCSV = True
        Exit Function
    End If

    ' Find actual last row and column with data
    lastRow = ws.Cells.Find(What:="*", After:=ws.Cells(1, 1), _
                            LookIn:=xlFormulas, LookAt:=xlPart, _
                            SearchOrder:=xlByRows, SearchDirection:=xlPrevious).row
    lastCol = ws.Cells.Find(What:="*", After:=ws.Cells(1, 1), _
                            LookIn:=xlFormulas, LookAt:=xlPart, _
                            SearchOrder:=xlByColumns, SearchDirection:=xlPrevious).Column

    ' Build CSV content
    csvContent = ""

    For row = 1 To lastRow
        rowData = ""

        For col = 1 To lastCol
            ' Get cell value and format for CSV
            cellValue = FormatCellForCSV(ws.Cells(row, col))

            ' Append to row with delimiter
            If col > 1 Then
                rowData = rowData & CSV_DELIMITER
            End If
            rowData = rowData & cellValue
        Next col

        ' Append row with line break
        csvContent = csvContent & rowData & vbCrLf
    Next row

    ' Write to file using ADODB.Stream for UTF-8 encoding
    Set stream = CreateObject("ADODB.Stream")

    With stream
        .Type = 2  ' adTypeText
        .Charset = "UTF-8"
        .Open
        .WriteText csvContent

        ' Remove BOM by re-reading without it
        .Position = 0
        .Type = 1  ' adTypeBinary
        .Position = 3  ' Skip UTF-8 BOM (3 bytes)

        Dim binaryContent As Variant
        binaryContent = .Read
        .Close

        ' Write without BOM
        .Open
        .Type = 1  ' adTypeBinary
        .Write binaryContent
        .SaveToFile filePath, 2  ' adSaveCreateOverWrite
        .Close
    End With

    Set stream = Nothing
    ExportWorksheetToCSV = True
    Exit Function

ErrorHandler:
    ExportWorksheetToCSV = False
    Debug.Print "Error exporting " & ws.Name & ": " & Err.Description
End Function

'''
' Formats a cell value for CSV output, handling special characters.
'
' @param cell The cell to format
' @return String CSV-safe value
'''
Private Function FormatCellForCSV(cell As Range) As String
    Dim value As String
    Dim needsQuotes As Boolean

    ' Get display value (respects number formatting)
    If IsEmpty(cell) Then
        FormatCellForCSV = ""
        Exit Function
    End If

    ' Use Text property to get formatted value, fall back to Value
    On Error Resume Next
    value = cell.Text
    If Len(value) = 0 And Not IsEmpty(cell.value) Then
        value = CStr(cell.value)
    End If
    On Error GoTo 0

    ' Handle null
    If IsNull(value) Then
        FormatCellForCSV = ""
        Exit Function
    End If

    ' Check if quoting is needed
    needsQuotes = False

    ' Quote if contains delimiter, quotes, or line breaks
    If InStr(value, CSV_DELIMITER) > 0 Then needsQuotes = True
    If InStr(value, """") > 0 Then needsQuotes = True
    If InStr(value, vbCr) > 0 Then needsQuotes = True
    If InStr(value, vbLf) > 0 Then needsQuotes = True

    ' Escape existing quotes by doubling them
    If InStr(value, """") > 0 Then
        value = Replace(value, """", """""")
    End If

    ' Wrap in quotes if needed
    If needsQuotes Then
        value = """" & value & """"
    End If

    FormatCellForCSV = value
End Function

'''
' Gets the workbook base name without extension.
'
' @return String Workbook name without .xlsx/.xlsm extension
'''
Private Function GetWorkbookBaseName() As String
    Dim name As String
    Dim dotPos As Long

    name = ThisWorkbook.name

    ' Remove extension
    dotPos = InStrRev(name, ".")
    If dotPos > 0 Then
        name = Left(name, dotPos - 1)
    End If

    GetWorkbookBaseName = name
End Function

'''
' Sanitizes a string for use as a filename.
' Replaces spaces with underscores and removes invalid characters.
'
' @param fileName The string to sanitize
' @return String Safe filename
'''
Private Function SanitizeFileName(fileName As String) As String
    Dim result As String
    Dim i As Long
    Dim char As String
    Dim invalidChars As String

    ' Characters not allowed in Windows filenames
    invalidChars = "\/:*?""<>|"

    result = fileName

    ' Replace spaces with underscores
    result = Replace(result, " ", "_")

    ' Remove invalid characters
    For i = 1 To Len(invalidChars)
        char = Mid(invalidChars, i, 1)
        result = Replace(result, char, "")
    Next i

    ' Remove leading/trailing underscores
    Do While Left(result, 1) = "_"
        result = Mid(result, 2)
    Loop
    Do While Right(result, 1) = "_"
        result = Left(result, Len(result) - 1)
    Loop

    ' Ensure not empty
    If Len(result) = 0 Then
        result = "Sheet"
    End If

    SanitizeFileName = result
End Function

'===============================================================================
' ThisWorkbook Event Handler (COPY THIS TO ThisWorkbook MODULE)
'===============================================================================
' Copy the code below into the ThisWorkbook module to enable auto-export on save.
'
' Private Sub Workbook_BeforeSave(ByVal SaveAsUI As Boolean, Cancel As Boolean)
'     ' Auto-export all sheets to CSV (silent mode)
'     CSVAutoExport.ExportAllSheetsToCSV ShowMessage:=False
' End Sub
'
' Private Sub Workbook_Open()
'     ' Assign keyboard shortcut when workbook opens
'     CSVAutoExport.AssignKeyboardShortcut
' End Sub
'===============================================================================
