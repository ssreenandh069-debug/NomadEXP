/* 
C program that uses NTFS MFT to search through
files on the system and gives you file names and
location faster than windows explorer
*/
#include <windows.h>
#include <winioctl.h>
#include <stdio.h>
#include <wchar.h>
#include <wctype.h>

typedef void (*FoundCallback)(const wchar_t* fileName, const wchar_t* fullPath);

volatile int g_cancel_search = 0;

__declspec(dllexport) void CancelSearch() {
    g_cancel_search = 1;
}

wchar_t* stristr(const wchar_t* str1, const wchar_t* str2) {
    if (!*str2) return (wchar_t*)str1;
    for (; *str1; ++str1) {
        if (towlower(*str1) == towlower(*str2)) {
            const wchar_t* h = str1;
            const wchar_t* n = str2;
            while (*h && *n && towlower(*h) == towlower(*n)) {
                ++h; ++n;
            }
            if (!*n) return (wchar_t*)str1;
        }
    }
    return NULL;
}

int IsMatch(wchar_t* fileFromDrive, wchar_t* userInput, wchar_t* requiredExt) {
    if (!userInput || !*userInput) return 0;
    
    // check if the file exists
    if (stristr(fileFromDrive, userInput) == NULL) {
        return 0; //bhak bsdk 
    }
    
    //checks the entension asked for
    if (requiredExt && wcslen(requiredExt) > 0) {
        wchar_t* ext = wcsrchr(fileFromDrive, L'.');
        if (!ext || _wcsicmp(ext, requiredExt) != 0) {
            return 0;
        }
    }
    
    return 1; // It's a perfect match!
}

void PathToId(HANDLE hPass, DWORDLONG fileID, wchar_t* outPath, DWORD maxChars) {
    FILE_ID_DESCRIPTOR fileDesc = { 0 };
    fileDesc.dwSize = sizeof(FILE_ID_DESCRIPTOR);
    fileDesc.Type = FileIdType;
    fileDesc.FileId.QuadPart = fileID;

    HANDLE hFile = OpenFileById(hPass, &fileDesc, GENERIC_READ, 
                                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, 
                                NULL, 0);

    if (hFile != INVALID_HANDLE_VALUE) {
        wchar_t tempPath[MAX_PATH];
        if (GetFinalPathNameByHandleW(hFile, tempPath, MAX_PATH, VOLUME_NAME_DOS)) {
            wcsncpy(outPath, tempPath + 4, maxChars);
        } else {
            wcscpy(outPath, L"Unknown Path");
        }
        CloseHandle(hFile);
    } else {
        wcscpy(outPath, L"Unknown Path");
    }
}

// scanner
int ScanFile(wchar_t* devicePath, wchar_t* targetFileName, wchar_t* extFilter , FoundCallback callback) {
    HANDLE hPass = CreateFileW(devicePath, GENERIC_READ, 
                              FILE_SHARE_READ | FILE_SHARE_WRITE, 
                              NULL, OPEN_EXISTING, 0, NULL);
                              
    if (hPass == INVALID_HANDLE_VALUE) {
        //ADMIN DE BHAIII
        return 0;
    }

    MFT_ENUM_DATA mftSearch;
    mftSearch.StartFileReferenceNumber = 0;
    mftSearch.LowUsn = 0;
    mftSearch.HighUsn = MAXLONGLONG;

    char buffer[65536]; 
    DWORD bytesReturned;
    int matchCount = 0;

    while (DeviceIoControl(hPass, FSCTL_ENUM_USN_DATA, 
                           &mftSearch, sizeof(mftSearch), 
                           buffer, sizeof(buffer), 
                           &bytesReturned, NULL)) 
    {
        
        USN nextUSN = *((USN*)buffer); 
        USN_RECORD* record = (USN_RECORD*)(buffer + sizeof(USN));
        if (g_cancel_search) break; 
        while ((char*)record < buffer + bytesReturned) {
            if (g_cancel_search) break; 
            wchar_t currentName[MAX_PATH];
            int nameLenChars = record->FileNameLength / sizeof(wchar_t);
            wcsncpy(currentName, (wchar_t*)((char*)record + record->FileNameOffset), nameLenChars);
            currentName[nameLenChars] = L'\0';

            if (IsMatch(currentName, targetFileName , extFilter)) {
                wchar_t fullPath[MAX_PATH];
                PathToId(hPass, record->FileReferenceNumber, fullPath, MAX_PATH);
                
                if (callback != NULL) {
                    callback(currentName, fullPath);
                }
                
                matchCount++;
            }

            record = (USN_RECORD*)((char*)record + record->RecordLength);
        }
        mftSearch.StartFileReferenceNumber = nextUSN; 
    }

    CloseHandle(hPass);
    return matchCount;
}

// scan all drives
void ScanDrive(wchar_t* targetFileName,wchar_t* extFilter, FoundCallback callback) {
    wchar_t drives[256];
    DWORD len = GetLogicalDriveStringsW(256, drives);
    
    if (len == 0) return;

    int totalMatches = 0;
    wchar_t* currentDrive = drives;

    while (*currentDrive) {
        wchar_t fileSystemName[MAX_PATH];
        if (GetVolumeInformationW(currentDrive, NULL, 0, NULL, NULL, NULL, fileSystemName, MAX_PATH)) {
            if (wcscmp(fileSystemName, L"NTFS") == 0) {
                wchar_t devicePath[MAX_PATH] = L"\\\\.\\X:";
                devicePath[4] = currentDrive[0]; 

                ScanFile(devicePath, targetFileName, extFilter, callback); 
            }
        }
        currentDrive += wcslen(currentDrive) + 1;
    }
}

__declspec(dllexport) void RunSearch(wchar_t* targetFileName, wchar_t* extFilter, FoundCallback pythonCallback) {
    g_cancel_search = 0; // Reset flag
    ScanDrive(targetFileName, extFilter, pythonCallback);
}
/* int main() {
    wchar_t searchScope[MAX_PATH];
    wchar_t userInput[MAX_PATH];

    while (1) {
        wprintf(L"\n==================================\n");
        wprintf(L"   TARGETED LIGHTNING SCANNER     \n");
        wprintf(L"==================================\n");
        
        wprintf(L"Where to search? (Type 'ALL' for everywhere, or 'C:', or 'C:\\Users'):\n> ");
        fgetws(searchScope, MAX_PATH, stdin);
        searchScope[wcscspn(searchScope, L"\r\n")] = L'\0';

        if (_wcsicmp(searchScope, L"exit") == 0) break;

        wprintf(L"Enter a file name to find:\n> ");
        fgetws(userInput, MAX_PATH, stdin);
        userInput[wcscspn(userInput, L"\r\n")] = L'\0';

        if (_wcsicmp(userInput, L"exit") == 0) break;

        if (wcslen(userInput) > 0) {
            
            if (_wcsicmp(searchScope, L"ALL") == 0 || wcslen(searchScope) == 0) {
                ScanDrive(userInput);
            } 
            
            else {
                wchar_t devicePath[MAX_PATH] = L"\\\\.\\X:";
                devicePath[4] = towupper(searchScope[0]); 

                wprintf(L"\n[*] Scanning location: %s ...\n", searchScope);
                int total = ScanFile(devicePath, userInput, searchScope);
                
                wprintf(L"\n==================================================\n");
                wprintf(L" SCAN COMPLETE! Total matches in location: %d\n", total);
                wprintf(L"==================================================\n");
            }
        }
    }

    return 0;
} */