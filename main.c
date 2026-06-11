#include <windows.h>
#include <winioctl.h>
#include <stdio.h>
#include <wchar.h>
#include <wctype.h>

int IsMatch(wchar_t* fileFromDrive, wchar_t* userInput) {
    if (!*userInput) return 0;
    
    wchar_t* p1 = fileFromDrive;
    wchar_t* p2 = userInput;
    
    while (*p1 && *p2 && towlower(*p1) == towlower(*p2)) {
        p1++;
        p2++;
    }
    
    if (!*p2) return 1; //okay coleslawg
    return 0; //nuh uh bitch
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
int ScanFile(wchar_t* devicePath, wchar_t* targetFileName, wchar_t* folderFilter) {
    HANDLE hPass = CreateFileW(devicePath, GENERIC_READ, 
                              FILE_SHARE_READ | FILE_SHARE_WRITE, 
                              NULL, OPEN_EXISTING, 0, NULL);
                              
    if (hPass == INVALID_HANDLE_VALUE) {
        wprintf(L"ADMIN DE LAUDEE\n", devicePath);
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

        while ((char*)record < buffer + bytesReturned) {
            wchar_t currentName[MAX_PATH];
            int nameLenChars = record->FileNameLength / sizeof(wchar_t);
            wcsncpy(currentName, (wchar_t*)((char*)record + record->FileNameOffset), nameLenChars);
            currentName[nameLenChars] = L'\0';

            if (IsMatch(currentName, targetFileName)) {
                wchar_t fullPath[MAX_PATH];
                PathToId(hPass, record->FileReferenceNumber, fullPath, MAX_PATH);

                if (folderFilter != NULL && wcslen(folderFilter) > 0) {
                    size_t filterLen = wcslen(folderFilter);
                    
                    if (_wcsnicmp(fullPath, folderFilter, filterLen) != 0) {
                        goto next_record; 
                    }
                }

                matchCount++;
                wprintf(L"\n   --> Found Match #%d\n", matchCount);
                wprintf(L"   Name: %s\n", currentName);
                wprintf(L"   Path: %s\n", fullPath);
            }

        next_record:
            record = (USN_RECORD*)((char*)record + record->RecordLength);
        }
        mftSearch.StartFileReferenceNumber = nextUSN; 
    }

    CloseHandle(hPass);
    return matchCount;
}

// scan all drives
void ScanDrive(wchar_t* targetFileName) {
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

                wprintf(L"\n[*] Scanning drive %s ...\n", devicePath);
                
                totalMatches += ScanFile(devicePath, targetFileName, NULL);
            }
        }
        currentDrive += wcslen(currentDrive) + 1;
    }

    wprintf(L"\n==================================================\n");
    wprintf(L" SCAN COMPLETE! Total matching files found: %d\n", totalMatches);
    wprintf(L"==================================================\n");
}

int main() {
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
}