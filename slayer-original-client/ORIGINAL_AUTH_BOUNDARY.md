# Slayer Legend 700.0.4 — ORIGINAL Unity client

Status: **No modified game APK exists.** This branch is only about the original client. It deliberately does not include the standalone Android login demo, game assets, XAPK, keys or user tokens.

## Confirmed from original XAPK (Bước 35)

| Method | IL2CPP virtual address |
|---|---|
| SignManager.TapToStart_Check | 0x529F7C0 |
| SignManager.AnonymousLogin_Button | 0x52A2010 |
| FirebaseManager.SignInGuest | 0x4CDB980 |
| SignManager.Migration_Anony_Login | 0x52A2118 |
| SignManager.Migration_Anony_Login_Result | 0x52A21C8 |
| SignManager.LoginResult_Func | 0x52A13BC |
| SignManager.LoadUserInfo | 0x52A31EC |

These are **virtual addresses**, not file offsets or tested live hooks. IFix may override native implementations.

## Confirmed from original game run (2026-11-05)

1. 05:46:43 — Button_TapToStart, Firebase token, LookupLoginConnect.
2. 05:46:43 — lookup host: integration-grpc-http2-api.gear2slayer.com.
3. 05:46:44 — front host: product-au-slayer-front.gear2slayer.com.
4. 05:46:44 — IFix Patch result: True.
5. 05:46:46 — ValidateAuthAsyncV3 -> SignManager.LoginResult_Func -> UserInfoLoad.Load.
6. 05:46:46 — BigIntegerCurrency type [None] not found.
7. 05:46:48 — realtime OnConnected via SignalR.
8. 05:46:50 — SceneTitle destroyed; original client proceeds past login.

This was the **original Google-account path**, not a working private-account test.

## Integration boundary

A replacement username/password screen is not sufficient. An authorized private build must integrate with the Unity SignManager and produce valid compatible responses for LookupLogin, ValidateAuthAsyncV3, SignIn/ LoginResponse and UserInfo load before showing the original game scene.

Still missing: original client patch, runtime test of re-signed APK/LIAPP, protobuf wire messages, private backend response compatibility, game state initialization, tested APK. Do not redirect the production client to an invented endpoint or call the standalone demo a game.
