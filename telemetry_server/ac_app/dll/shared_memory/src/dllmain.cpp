// #include "MinHook.h"
// #include <string>
// #include <windows.h>
//
// // Typedef for the real CreateFileMappingW function
// // This matches the exact signature from Windows API
// using CreateFileMappingW_t = HANDLE(WINAPI *)(HANDLE, LPSECURITY_ATTRIBUTES,
//                                               DWORD, DWORD, DWORD, LPCWSTR);
//
// // Typedef for the real OpenFileMappingW function
// using OpenFileMappingW_t = HANDLE(WINAPI *)(DWORD, BOOL, LPCWSTR);
//
// // Pointers that will hold the ORIGINAL (unhooked) functions
// CreateFileMappingW_t Real_CreateFileMappingW = nullptr;
// OpenFileMappingW_t Real_OpenFileMappingW = nullptr;
//
// // Returns a suffix like "_1", "_2", etc. based on environment variable
// // This lets you run multiple instances with different shared memory names
// std::wstring instance_suffix() {
//   wchar_t buf[32]{};
//
//   // Read environment variable AC_INSTANCE_ID
//   // Example: set AC_INSTANCE_ID=1
//   GetEnvironmentVariableW(L"AC_INSTANCE_ID", buf, 32);
//
//   // If not set, default to "_0"
//   if (wcslen(buf) == 0)
//     return L"_0";
//
//   // Otherwise return "_" + value (e.g., "_1")
//   return std::wstring(L"_") + buf;
// }
//
// // Rewrites shared memory names to make them unique per instance
// std::wstring rewrite_name(LPCWSTR name) {
//   // If no name was provided, do nothing
//   if (!name)
//     return L"";
//
//   std::wstring s = name;
//
//   // These are the shared memory names used by Assetto Corsa
//   // We append a suffix so each instance gets its own memory
//   if (s == L"Local\\acpmf_physics")
//     return s + instance_suffix();
//
//   if (s == L"Local\\acpmf_graphics")
//     return s + instance_suffix();
//
//   if (s == L"Local\\acpmf_static")
//     return s + instance_suffix();
//
//   // If it's not one of the known names, leave it unchanged
//   return s;
// }
//
// // Hooked version of CreateFileMappingW
// // This gets called instead of the real one after hooking
// HANDLE WINAPI Hook_CreateFileMappingW(HANDLE hFile,
//                                       LPSECURITY_ATTRIBUTES lpAttributes,
//                                       DWORD flProtect, DWORD
//                                       dwMaximumSizeHigh, DWORD
//                                       dwMaximumSizeLow, LPCWSTR lpName) {
//   // Potentially rewrite the shared memory name
//   std::wstring new_name = rewrite_name(lpName);
//
//   // Call the REAL function with either:
//   // - modified name (if we changed it)
//   // - original name (if unchanged)
//   return Real_CreateFileMappingW(hFile, lpAttributes, flProtect,
//                                  dwMaximumSizeHigh, dwMaximumSizeLow,
//                                  new_name.empty() ? lpName :
//                                  new_name.c_str());
// }
//
// // Hooked version of OpenFileMappingW
// HANDLE WINAPI Hook_OpenFileMappingW(DWORD dwDesiredAccess, BOOL
// bInheritHandle,
//                                     LPCWSTR lpName) {
//   // Same idea as above: rewrite name if needed
//   std::wstring new_name = rewrite_name(lpName);
//
//   return Real_OpenFileMappingW(dwDesiredAccess, bInheritHandle,
//                                new_name.empty() ? lpName : new_name.c_str());
// }
//
// // This runs in a separate thread to install hooks
// // Important: we avoid doing heavy work in DllMain
// DWORD WINAPI InitHooks(LPVOID) {
//   MH_Initialize();
//
//   MH_CreateHookApi(L"kernel32.dll", "CreateFileMappingW",
//                    reinterpret_cast<LPVOID>(Hook_CreateFileMappingW),
//                    reinterpret_cast<LPVOID *>(&Real_CreateFileMappingW));
//
//   MH_CreateHookApi(L"kernel32.dll", "OpenFileMappingW",
//                    reinterpret_cast<LPVOID>(Hook_OpenFileMappingW),
//                    reinterpret_cast<LPVOID *>(&Real_OpenFileMappingW));
//
//   MH_EnableHook(MH_ALL_HOOKS);
//
//   return 0;
// }
//
// // Entry point of the DLL
// BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID) {
//   if (reason == DLL_PROCESS_ATTACH) {
//     // Prevent DLL_THREAD_ATTACH / DETACH notifications
//     // This reduces overhead and avoids complexity
//     DisableThreadLibraryCalls(hModule);
//
//     // VERY IMPORTANT:
//     // We do NOT install hooks directly in DllMain
//     // because it can cause deadlocks or crashes
//     //
//     // Instead, we spawn a new thread to do it safely
//     CreateThread(nullptr, 0, InitHooks, nullptr, 0, nullptr);
//   }
//
//   return TRUE;
// }

#include "MinHook.h"
#include <cstring>
#include <string>
#include <winbase.h>
#include <windows.h>

bool MappingExists(const char *name) {
  HANDLE h = OpenFileMappingA(FILE_MAP_READ, FALSE, name);

  if (h) {
    CloseHandle(h);
    return true;
  }

  return false;
}

int GetInstanceId() {
  char buffer[32] = {0};
  GetPrivateProfileString(
      "NETWORK", "ID", "0", buffer, sizeof(buffer),
      ".\\apps\\python\\telemetry_server\\telemetry_server.ini");

  return atoi(buffer);
}

using CreateFileMappingA_t = HANDLE(WINAPI *)(HANDLE, LPSECURITY_ATTRIBUTES,
                                              DWORD, DWORD, DWORD, LPCSTR);
using OpenFileMappingA_t = HANDLE(WINAPI *)(DWORD, BOOL, LPCSTR);

using CreateFileMappingW_t = HANDLE(WINAPI *)(HANDLE, LPSECURITY_ATTRIBUTES,
                                              DWORD, DWORD, DWORD, LPCWSTR);
using OpenFileMappingW_t = HANDLE(WINAPI *)(DWORD, BOOL, LPCWSTR);

CreateFileMappingA_t fpCreateFileMappingA = nullptr;
OpenFileMappingA_t fpOpenFileMappingA = nullptr;
CreateFileMappingW_t fpCreateFileMappingW = nullptr;
OpenFileMappingW_t fpOpenFileMappingW = nullptr;

HANDLE WINAPI hkCreateFileMappingA(HANDLE hFile,
                                   LPSECURITY_ATTRIBUTES lpAttributes,
                                   DWORD flProtect, DWORD dwMaxSizeHigh,
                                   DWORD dwMaxSizeLow, LPCSTR lpName) {
  if (lpName && strstr(lpName, "acpmf")) {
    char newName[128];
    sprintf(newName, "%s_%d", lpName, GetInstanceId());
    // std::string message = "Original name: " + std::string(lpName) +
    //                       " New name: " + std::string(newName);
    // MessageBoxA(nullptr, message.c_str(), "CreateFileMappingA", MB_OK);
    return fpCreateFileMappingA(hFile, lpAttributes, flProtect, dwMaxSizeHigh,
                                dwMaxSizeLow, newName);
  }

  // MessageBoxA(nullptr, lpName, "CreateFileMappingA", MB_OK);
  return fpCreateFileMappingA(hFile, lpAttributes, flProtect, dwMaxSizeHigh,
                              dwMaxSizeLow, lpName);
}

HANDLE WINAPI hkOpenFileMappingA(DWORD dwDesiredAccess, BOOL bInheritHandle,
                                 LPCSTR lpName) {

  if (lpName && strstr(lpName, "acpmf")) {
    char newName[128];
    sprintf(newName, "%s_%d", lpName, GetInstanceId());
    // std::string message = "Original name: " + std::string(lpName) +
    //                       " New name: " + std::string(newName);
    // MessageBoxA(nullptr, message.c_str(), "OpenFileMappingA", MB_OK);
    return fpOpenFileMappingA(dwDesiredAccess, bInheritHandle, newName);
  }

  // MessageBoxA(nullptr, lpName, "OpenFileMappingA", MB_OK);
  return fpOpenFileMappingA(dwDesiredAccess, bInheritHandle, lpName);
}

HANDLE WINAPI hkCreateFileMappingW(HANDLE hFile,
                                   LPSECURITY_ATTRIBUTES lpAttributes,
                                   DWORD flProtect, DWORD dwMaxSizeHigh,
                                   DWORD dwMaxSizeLow, LPCWSTR lpName) {
  if (lpName && wcsstr(lpName, L"acpmf")) {
    wchar_t newName[128];
    swprintf(newName, 128, L"%ls_%d", lpName, GetInstanceId());

    // wchar_t message[512];
    // swprintf(message, 512, L"Original name: %ls\nNew name: %ls", lpName,
    //          newName);
    // MessageBoxW(nullptr, message, L"CreateFileMappingW", MB_OK);

    return fpCreateFileMappingW(hFile, lpAttributes, flProtect, dwMaxSizeHigh,
                                dwMaxSizeLow,
                                newName // change to newName when redirecting
    );
  }

  return fpCreateFileMappingW(hFile, lpAttributes, flProtect, dwMaxSizeHigh,
                              dwMaxSizeLow, lpName);
}

HANDLE WINAPI hkOpenFileMappingW(DWORD dwDesiredAccess, BOOL bInheritHandle,
                                 LPCWSTR lpName) {
  if (lpName && wcsstr(lpName, L"acpmf")) {
    wchar_t newName[128];
    swprintf(newName, 128, L"%ls_%d", lpName, GetInstanceId());

    // wchar_t message[512];
    // swprintf(message, 512, L"Original name: %ls\nNew name: %ls", lpName,
    //          newName);
    // MessageBoxW(nullptr, message, L"OpenFileMappingW", MB_OK);

    return fpOpenFileMappingW(dwDesiredAccess, bInheritHandle,
                              newName // change to newName when redirecting
    );
  }

  return fpOpenFileMappingW(dwDesiredAccess, bInheritHandle, lpName);
}

DWORD WINAPI InitThread(LPVOID) {
  if (MH_Initialize() != MH_OK) {
    MessageBoxA(nullptr, "Failed to initialize minhook", "Debug", MB_OK);
    return 1;
  }

  HMODULE hKernel32 = GetModuleHandleA("kernel32.dll");
  if (!hKernel32) {
    MessageBoxA(nullptr, "GetModuleHandleA(kernel32.dll) failed", "Debug",
                MB_OK);
    return 1;
  }

  auto pCreateA =
      reinterpret_cast<void *>(GetProcAddress(hKernel32, "CreateFileMappingA"));

  auto pOpenA =
      reinterpret_cast<void *>(GetProcAddress(hKernel32, "OpenFileMappingA"));

  auto pCreateW =
      reinterpret_cast<void *>(GetProcAddress(hKernel32, "CreateFileMappingW"));

  auto pOpenW =
      reinterpret_cast<void *>(GetProcAddress(hKernel32, "OpenFileMappingW"));

  if (!pCreateA || !pOpenA || !pCreateW || !pOpenW)
    return 1;

  MH_CreateHook(pCreateA, reinterpret_cast<void *>(&hkCreateFileMappingA),
                reinterpret_cast<void **>(&fpCreateFileMappingA));

  MH_CreateHook(pOpenA, reinterpret_cast<void *>(&hkOpenFileMappingA),
                reinterpret_cast<void **>(&fpOpenFileMappingA));

  MH_CreateHook(pCreateW, (void *)(&hkCreateFileMappingW),
                (void **)(&fpCreateFileMappingW));

  MH_CreateHook(pOpenW, reinterpret_cast<void *>(&hkOpenFileMappingW),
                reinterpret_cast<void **>(&fpOpenFileMappingW));

  MH_EnableHook(MH_ALL_HOOKS);

  return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID) {
  if (reason == DLL_PROCESS_ATTACH) {
    DisableThreadLibraryCalls(hModule);
    CreateThread(nullptr, 0, InitThread, nullptr, 0, nullptr);
  }

  return TRUE;
}
