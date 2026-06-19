/* 
C program that uses NTFS MFT to search through
files on the system and gives you file names and
location faster than windows explorer
*/
#include <windows.h>
#include <winioctl.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include <wctype.h>

typedef void (*FoundCallback)(const wchar_t* fileName, const wchar_t* fullPath);

volatile int g_cancel_search = 0;

__declspec(dllexport) void CancelSearch() {
    g_cancel_search = 1;
}

typedef struct {
    size_t  nameOffset;
    DWORDLONG fileRef;
    wchar_t driveLetter;
} FileRecord;

wchar_t* g_stringArena = NULL;
size_t g_arenaCapacityChars = 0;
size_t g_arenaUsedChars = 0; 

FileRecord* g_fileCache = NULL;
int g_cacheCount = 0;
int g_cacheCapacity = 0;
HANDLE g_hFile = INVALID_HANDLE_VALUE;
HANDLE g_hMap = NULL;
void* g_mappedView = NULL;

FileRecord* g_deltaCache = NULL;
size_t g_deltaCacheCount = 0;
size_t g_deltaCacheCapacity = 0;

wchar_t* g_deltaArena = NULL;
size_t g_deltaArenaCapacity = 0;
size_t g_deltaArenaUsed = 0;

USN g_driveUSN[26] = {0};
DWORDLONG g_driveJournalId[26] = {0};

void AddToDelta(wchar_t* name, DWORDLONG ref, wchar_t drive) {
    if (g_deltaCacheCount >= g_deltaCacheCapacity) {
        g_deltaCacheCapacity = (g_deltaCacheCapacity == 0) ? 1000 : g_deltaCacheCapacity * 2;
        g_deltaCache = (FileRecord*)realloc(g_deltaCache, g_deltaCacheCapacity * sizeof(FileRecord));
    }
    
    size_t nameLen = wcslen(name) + 1;
    if (g_deltaArenaUsed + nameLen > g_deltaArenaCapacity) {
        g_deltaArenaCapacity = (g_deltaArenaCapacity == 0) ? 50000 : g_deltaArenaCapacity * 2;
        g_deltaArena = (wchar_t*)realloc(g_deltaArena, g_deltaArenaCapacity * sizeof(wchar_t));
    }
    
    wchar_t* dest = g_deltaArena + g_deltaArenaUsed;
    wcsncpy(dest, name, nameLen);
    _wcslwr(dest);
    
    g_deltaCache[g_deltaCacheCount].nameOffset = g_deltaArenaUsed;
    g_deltaCache[g_deltaCacheCount].fileRef = ref;
    g_deltaCache[g_deltaCacheCount].driveLetter = drive;
    
    g_deltaArenaUsed += nameLen;
    g_deltaCacheCount++;
}

void AddToCache(wchar_t* name, DWORDLONG ref, wchar_t drive) {
    if (g_cacheCount >= g_cacheCapacity) {
        g_cacheCapacity = (g_cacheCapacity == 0) ? 500000 : g_cacheCapacity * 2;
        g_fileCache = (FileRecord*)realloc(g_fileCache, g_cacheCapacity * sizeof(FileRecord));
    }
    
    size_t nameLen = wcslen(name) + 1; 
    
    if (g_arenaUsedChars + nameLen > g_arenaCapacityChars) {
        g_arenaCapacityChars = (g_arenaCapacityChars == 0) ? 10000000 : g_arenaCapacityChars * 2;
        g_stringArena = (wchar_t*)realloc(g_stringArena, g_arenaCapacityChars * sizeof(wchar_t));
    }
    
    wchar_t* destination = g_stringArena + g_arenaUsedChars;
    wcsncpy(destination, name, nameLen);
    _wcslwr(destination); 
    
    g_fileCache[g_cacheCount].nameOffset = g_arenaUsedChars;
    g_fileCache[g_cacheCount].fileRef = ref;
    g_fileCache[g_cacheCount].driveLetter = drive;
    
    g_arenaUsedChars += nameLen;
    g_cacheCount++;
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

int IsMatchFast(wchar_t* recordName, wchar_t* lowerInput, wchar_t* lowerExt) {
    if (!lowerInput || !*lowerInput) return 0;
    
    if (wcsstr(recordName, lowerInput) == NULL) {
        return 0; 
    }
    
    if (lowerExt && *lowerExt) {
        wchar_t* ext = wcsrchr(recordName, L'.');
        if (!ext || wcscmp(ext, lowerExt) != 0) {
            return 0;
        }
    }
    return 1;
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

void ScanFile(wchar_t* devicePath, wchar_t driveLetter) {
    HANDLE hPass = CreateFileW(devicePath, GENERIC_READ, 
                              FILE_SHARE_READ | FILE_SHARE_WRITE, 
                              NULL, OPEN_EXISTING, 0, NULL);
                              
    if (hPass == INVALID_HANDLE_VALUE) {
        return;
    }

    MFT_ENUM_DATA mftSearch;
    mftSearch.StartFileReferenceNumber = 0;
    mftSearch.LowUsn = 0;
    mftSearch.HighUsn = MAXLONGLONG;

    char buffer[65536]; 
    DWORD bytesReturned;

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

            AddToCache(currentName, record->FileReferenceNumber, driveLetter);

            record = (USN_RECORD*)((char*)record + record->RecordLength);
        }
        mftSearch.StartFileReferenceNumber = nextUSN;
    }

    USN_JOURNAL_DATA journalData;
    if (DeviceIoControl(hPass, FSCTL_QUERY_USN_JOURNAL, NULL, 0, &journalData, sizeof(journalData), &bytesReturned, NULL)) {
        int dIdx = towupper(driveLetter) - L'A';
        g_driveUSN[dIdx] = journalData.NextUsn;
        g_driveJournalId[dIdx] = journalData.UsnJournalID; 
    }

    CloseHandle(hPass);
}

void ScanDrive() {
    wchar_t drives[256];
    DWORD len = GetLogicalDriveStringsW(256, drives);
    if (len == 0) return;

    wchar_t* currentDrive = drives;
    while (*currentDrive) {
        wchar_t fileSystemName[MAX_PATH];
        if (GetVolumeInformationW(currentDrive, NULL, 0, NULL, NULL, NULL, fileSystemName, MAX_PATH)) {
            if (wcscmp(fileSystemName, L"NTFS") == 0) {
                wchar_t devicePath[MAX_PATH] = L"\\\\.\\X:";
                devicePath[4] = currentDrive[0]; 
                ScanFile(devicePath, currentDrive[0]); 
            }
        }
        currentDrive += wcslen(currentDrive) + 1;
    }
}

void SaveAndMapCache() {
    wchar_t cachePath[MAX_PATH];
    ExpandEnvironmentStringsW(L"%TEMP%\\nomad_cache.dat", cachePath, MAX_PATH);

    FILE* f = _wfopen(cachePath, L"wb");
    if (f) {
        fwrite(&g_cacheCount, sizeof(int), 1, f);
        fwrite(&g_arenaUsedChars, sizeof(size_t), 1, f);
        
        fwrite(g_fileCache, sizeof(FileRecord), g_cacheCount, f);
        fwrite(g_stringArena, sizeof(wchar_t), g_arenaUsedChars, f);
        fclose(f);
    }

    if (g_fileCache) free(g_fileCache);
    if (g_stringArena) free(g_stringArena);
    
    g_hFile = CreateFileW(cachePath, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (g_hFile != INVALID_HANDLE_VALUE) {
        g_hMap = CreateFileMappingW(g_hFile, NULL, PAGE_READONLY, 0, 0, NULL);
        if (g_hMap != NULL) {
            g_mappedView = MapViewOfFile(g_hMap, FILE_MAP_READ, 0, 0, 0);
            
            char* base = (char*)g_mappedView;
            base += sizeof(int) + sizeof(size_t); // Skip the header we wrote
            
            g_fileCache = (FileRecord*)base;
            g_stringArena = (wchar_t*)(base + (g_cacheCount * sizeof(FileRecord)));
        }
    }
}

__declspec(dllexport) void CloseIndex() {
    if (g_mappedView) {
        UnmapViewOfFile(g_mappedView);
        g_mappedView = NULL;
    }
    if (g_hMap) {
        CloseHandle(g_hMap);
        g_hMap = NULL;
    }
    if (g_hFile != INVALID_HANDLE_VALUE) {
        CloseHandle(g_hFile);
        g_hFile = INVALID_HANDLE_VALUE;
    }
    
    g_fileCache = NULL;
    g_stringArena = NULL;
    g_cacheCount = 0;
    g_arenaUsedChars = 0;
}

__declspec(dllexport) void BuildIndex() {
    if (g_deltaCache) free(g_deltaCache);
    if (g_deltaArena) free(g_deltaArena);
    g_deltaCache = NULL; 
    g_deltaArena = NULL;
    g_deltaCacheCount = 0; 
    g_deltaArenaUsed = 0; 
    g_deltaArenaCapacity = 0; 
    g_deltaCacheCapacity = 0;
    
    CloseIndex();
    
    g_arenaCapacityChars = 0;
    g_cacheCapacity = 0;
    
    ScanDrive(); 
    SaveAndMapCache();
}

__declspec(dllexport) void RunSearch(wchar_t* targetFileName, wchar_t* extFilter, FoundCallback pythonCallback) {
    g_cancel_search = 0;
    
    int resolved_count = 0; 
    const int MAX_RESULTS = 150; 

    wchar_t lowerTarget[MAX_PATH] = L"";
    if (targetFileName) {
        wcsncpy(lowerTarget, targetFileName, MAX_PATH);
        _wcslwr(lowerTarget);
    }

    wchar_t lowerExt[MAX_PATH] = L"";
    if (extFilter) {
        wcsncpy(lowerExt, extFilter, MAX_PATH);
        _wcslwr(lowerExt);
    }

    HANDLE driveHandles[26] = {0};

    for (int i = 0; i < g_cacheCount; i++) {
        if (g_cancel_search) break;
        if (resolved_count >= MAX_RESULTS) break;
        wchar_t* currentName = g_stringArena + g_fileCache[i].nameOffset;
        if (IsMatchFast(currentName, lowerTarget, lowerExt)) {
            wchar_t fullPath[MAX_PATH];
            int driveIdx = towupper(g_fileCache[i].driveLetter) - L'A';
            if (driveIdx >= 0 && driveIdx < 26) {
                if (driveHandles[driveIdx] == 0 || driveHandles[driveIdx] == INVALID_HANDLE_VALUE) {
                    wchar_t devicePath[MAX_PATH] = L"\\\\.\\X:";
                    devicePath[4] = g_fileCache[i].driveLetter;
                    driveHandles[driveIdx] = CreateFileW(devicePath, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
                }
                if (driveHandles[driveIdx] != INVALID_HANDLE_VALUE) {
                    PathToId(driveHandles[driveIdx], g_fileCache[i].fileRef, fullPath, MAX_PATH);
                    if (pythonCallback != NULL) {
                        wchar_t* originalName = wcsrchr(fullPath, L'\\');
                        if (originalName != NULL) originalName++; else originalName = fullPath;
                        pythonCallback(originalName, fullPath);
                        resolved_count++; 
                    }
                }
            }
        }
    }

    for (int i = 0; i < g_deltaCacheCount; i++) {
        if (g_cancel_search) break;
        if (resolved_count >= MAX_RESULTS) break;
        
        wchar_t* currentName = g_deltaArena + g_deltaCache[i].nameOffset;
        
        if (IsMatchFast(currentName, lowerTarget, lowerExt)) {
            wchar_t fullPath[MAX_PATH];
            int driveIdx = towupper(g_deltaCache[i].driveLetter) - L'A';
            if (driveIdx >= 0 && driveIdx < 26) {
                if (driveHandles[driveIdx] == 0 || driveHandles[driveIdx] == INVALID_HANDLE_VALUE) {
                    wchar_t devicePath[MAX_PATH] = L"\\\\.\\X:";
                    devicePath[4] = g_deltaCache[i].driveLetter;
                    driveHandles[driveIdx] = CreateFileW(devicePath, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
                }
                if (driveHandles[driveIdx] != INVALID_HANDLE_VALUE) {
                    PathToId(driveHandles[driveIdx], g_deltaCache[i].fileRef, fullPath, MAX_PATH);
                    if (pythonCallback != NULL) {
                        wchar_t* originalName = wcsrchr(fullPath, L'\\');
                        if (originalName != NULL) originalName++; else originalName = fullPath;
                        pythonCallback(originalName, fullPath);
                        resolved_count++; 
                    }
                }
            }
        }
    }

    // Cleanup handles
    for (int i = 0; i < 26; i++) {
        if (driveHandles[i] != 0 && driveHandles[i] != INVALID_HANDLE_VALUE) {
            CloseHandle(driveHandles[i]);
        }
    }
}

__declspec(dllexport) int SyncDeltas() {
    wchar_t drives[256];
    GetLogicalDriveStringsW(256, drives);
    wchar_t* currentDrive = drives;

    while (*currentDrive) {
        int dIdx = towupper(currentDrive[0]) - L'A';
        if (g_driveUSN[dIdx] != 0) {
            wchar_t devicePath[MAX_PATH] = L"\\\\.\\X:";
            devicePath[4] = currentDrive[0];
            
            HANDLE hPass = CreateFileW(devicePath, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
            if (hPass != INVALID_HANDLE_VALUE) {
                READ_USN_JOURNAL_DATA readData = {0};
                readData.StartUsn = g_driveUSN[dIdx];
                readData.ReasonMask = USN_REASON_FILE_CREATE | USN_REASON_RENAME_NEW_NAME; 
                readData.ReturnOnlyOnClose = 0;
                readData.Timeout = 0;
                readData.BytesToWaitFor = 0;
                readData.UsnJournalID = g_driveJournalId[dIdx];

                char buffer[65536];
                DWORD bytesReturned;
                
                while (DeviceIoControl(hPass, FSCTL_READ_USN_JOURNAL, &readData, sizeof(readData), buffer, sizeof(buffer), &bytesReturned, NULL)) {
                    
                    if (bytesReturned <= sizeof(USN)) {
                        break; 
                    }

                    USN nextUSN = *((USN*)buffer);
                    USN_RECORD* record = (USN_RECORD*)(buffer + sizeof(USN));
                    
                    while ((char*)record < buffer + bytesReturned) {
                        wchar_t currentName[MAX_PATH];
                        int nameLenChars = record->FileNameLength / sizeof(wchar_t);
                        wcsncpy(currentName, (wchar_t*)((char*)record + record->FileNameOffset), nameLenChars);
                        currentName[nameLenChars] = L'\0';

                        AddToDelta(currentName, record->FileReferenceNumber, currentDrive[0]);

                        record = (USN_RECORD*)((char*)record + record->RecordLength);
                    }
                    readData.StartUsn = nextUSN;
                    g_driveUSN[dIdx] = nextUSN; 
                }
                CloseHandle(hPass);
            }
        }
        currentDrive += wcslen(currentDrive) + 1;
    }
    return (int)g_deltaCacheCount; 
}
