package com.slayerprivate.login;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;
import javax.net.ssl.HttpsURLConnection;

/** HTTPS account demo, not connected to the original Unity game. */
public final class RemoteAuthActivity extends Activity {
    private final ExecutorService workers = Executors.newSingleThreadExecutor();
    private static final int BG = Color.rgb(12,17,30);
    private static final int WHITE = Color.rgb(240,244,250);
    private static final int GOLD = Color.rgb(255,205,113);
    private static final int MUTED = Color.rgb(162,175,195);
    private static final int PANEL = Color.rgb(25,33,49);
    private TextView status;
    private EditText host, username, password;

    @Override public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        form();
    }

    private int dp(int x) {
        return (int)(getResources().getDisplayMetrics().density * x + .5f);
    }
    private LinearLayout.LayoutParams spacing(int top) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.topMargin = dp(top);
        return p;
    }
    private GradientDrawable bg(int color) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(12));
        return g;
    }
    private TextView txt(String val, int size, int color) {
        TextView v = new TextView(this);
        v.setText(val); v.setTextSize(size); v.setTextColor(color);
        return v;
    }
    private EditText input(String hint, boolean secret) {
        EditText e = new EditText(this);
        e.setTextSize(15);
        e.setSingleLine();
        e.setHint(hint);
        e.setTextColor(WHITE);
        e.setHintTextColor(MUTED);
        e.setBackground(bg(PANEL));
        e.setPadding(dp(14),dp(13),dp(14),dp(13));
        e.setInputType(secret ? (InputType.TYPE_CLASS_TEXT |
                InputType.TYPE_TEXT_VARIATION_PASSWORD) : InputType.TYPE_CLASS_TEXT);
        return e;
    }
    private Button button(String label, boolean primary) {
        Button b = new Button(this);
        b.setText(label); b.setAllCaps(false);
        b.setTextColor(primary ? BG : WHITE);
        b.setBackground(bg(primary ? GOLD : PANEL));
        b.setMinHeight(dp(48));
        return b;
    }
    private LinearLayout page() {
        LinearLayout l = new LinearLayout(this);
        l.setBackgroundColor(BG);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(24),dp(54),dp(24),dp(30));
        return l;
    }
    private void show(LinearLayout p) {
        ScrollView s = new ScrollView(this);
        s.setFillViewport(true);
        s.addView(p);
        setContentView(s);
    }
    private static String origin(String raw) throws Exception {
        URI uri = new URI(raw.trim());
        if (!"https".equalsIgnoreCase(uri.getScheme()) ||
            uri.getHost() == null || uri.getRawUserInfo() != null ||
            uri.getRawQuery() != null || uri.getRawFragment() != null ||
            !(uri.getRawPath() == null || uri.getRawPath().isEmpty() ||
              "/".equals(uri.getRawPath()))) {
            throw new IllegalArgumentException("Dùng URL HTTPS, ví dụ https://accounts.example.com");
        }
        return "https://" + uri.getRawAuthority();
    }
    private static JSONObject exchange(String base, String method, String path,
                                       JSONObject body, String bearer) throws Exception {
        HttpsURLConnection conn =
                (HttpsURLConnection)new URL(base + path).openConnection();
        conn.setConnectTimeout(12000);
        conn.setReadTimeout(12000);
        conn.setInstanceFollowRedirects(false);
        conn.setRequestMethod(method);
        conn.setRequestProperty("Accept","application/json");
        if (bearer != null) conn.setRequestProperty("Authorization","Bearer " + bearer);
        try {
            if (body != null) {
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type","application/json; charset=utf-8");
                byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
                try (OutputStream out = conn.getOutputStream()) { out.write(bytes); }
            }
            int code = conn.getResponseCode();
            InputStream stream = code >= 400 ? conn.getErrorStream() : conn.getInputStream();
            if (stream == null) throw new IllegalStateException("HTTP " + code);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (InputStream in = stream) {
                byte[] buf = new byte[4096]; int n;
                while ((n=in.read(buf))!=-1) {
                    output.write(buf,0,n);
                    if (output.size()>65536) throw new IllegalStateException("Response quá lớn");
                }
            }
            JSONObject response = new JSONObject(
                    new String(output.toByteArray(),StandardCharsets.UTF_8));
            if (code<200 || code>=300) throw new IllegalStateException(
                    "HTTP "+code+": "+response.optString("error","Server không chấp nhận"));
            return response;
        } finally { conn.disconnect(); }
    }
    private void execute(Callable<JSONObject> work, Consumer<JSONObject> onSuccess) {
        status.setText("Đang kết nối server...");
        workers.submit(() -> {
            try {
                JSONObject result=work.call();
                runOnUiThread(() -> { if (!isFinishing()) onSuccess.accept(result); });
            } catch (Exception e) {
                final String msg=e.getMessage()==null?"Kết nối thất bại":e.getMessage();
                runOnUiThread(() -> { if (!isFinishing()) status.setText("Lỗi: "+msg); });
            }
        });
    }
    private void form() {
        LinearLayout p=page();
        TextView title=txt("ĐĂNG NHẬP SERVER • V2",23,GOLD);
        title.setGravity(Gravity.CENTER_HORIZONTAL);
        p.addView(title);
        p.addView(txt("Chỉ dùng máy chủ riêng. Không kết nối game gốc.",13,MUTED),spacing(20));
        host=input("https://accounts.example.com",false);
        host.setText(getPreferences(MODE_PRIVATE).getString("backend",""));
        p.addView(host,spacing(28));
        username=input("Tên tài khoản",false);
        p.addView(username,spacing(14));
        password=input("Mật khẩu (12+ ký tự)",true);
        p.addView(password,spacing(14));
        status=txt("",14,GOLD);
        p.addView(status,spacing(16));
        Button register=button("Đăng ký server",false);
        p.addView(register,spacing(12));
        register.setOnClickListener(v -> login(true));
        Button signIn=button("Đăng nhập server",true);
        p.addView(signIn,spacing(12));
        signIn.setOnClickListener(v -> login(false));
        Button resume=button("Kiểm tra phiên đã lưu",false);
        p.addView(resume,spacing(12));
        resume.setOnClickListener(v -> {
            try {
                String base=origin(host.getText().toString());
                String token=TokenStore.load(this);
                if (token==null) { status.setText("Chưa có phiên đã lưu"); return; }
                execute(() -> exchange(base,"GET","/api/v1/auth/me",null,token),
                    data -> home(base,data.optString("username"),data.optLong("id")));
            } catch (Exception e) { status.setText(e.getMessage()); }
        });
        Button back=button("Quay về đăng nhập offline",false);
        p.addView(back,spacing(18));
        back.setOnClickListener(v -> finish());
        p.addView(txt("Không có backend được tự động triển khai. " +
                "Màn hình này cần máy chủ HTTPS riêng mới đăng nhập trực tuyến được.",
                12,MUTED),spacing(30));
        show(p);
    }
    private void login(boolean register) {
        final String base;
        try { base=origin(host.getText().toString()); }
        catch (Exception e) { status.setText(e.getMessage()); return; }
        final String user=username.getText().toString().trim().toLowerCase(Locale.ROOT);
        final String secret=password.getText().toString();
        password.setText("");
        if (!user.matches("[a-z0-9_]{3,24}") ||
            secret.length()<12 || secret.length()>128) {
            status.setText("Tên 3–24 ký tự và mật khẩu 12–128 ký tự");
            return;
        }
        execute(() -> {
            JSONObject data=new JSONObject();
            data.put("username",user);
            data.put("password",secret);
            return exchange(base,"POST",register?"/api/v1/auth/register":"/api/v1/auth/login",data,null);
        }, result -> {
            if (register) { status.setText("Tạo tài khoản thành công. Hãy đăng nhập."); return; }
            try {
                TokenStore.save(this,result.getString("accessToken"));
                getPreferences(MODE_PRIVATE).edit().putString("backend",base).apply();
                home(base,user,result.optLong("accountId"));
            } catch (Exception e) {
                status.setText("Không lưu được token trên thiết bị");
            }
        });
    }
    private void home(String base,String user,long id) {
        LinearLayout p=page();
        p.addView(txt("✓ ĐĂNG NHẬP SERVER THÀNH CÔNG",20,GOLD));
        p.addView(txt("Tài khoản: "+user,18,WHITE),spacing(28));
        p.addView(txt("Account ID: "+id,14,MUTED),spacing(12));
        p.addView(txt("Chưa kết nối vào nhân vật/gameplay Unity gốc.",14,MUTED),spacing(18));
        status=txt("",14,GOLD);
        p.addView(status,spacing(18));
        Button logout=button("Đăng xuất và thu hồi token",true);
        p.addView(logout,spacing(14));
        logout.setOnClickListener(v -> {
            String token=TokenStore.load(this);
            if (token==null) { form(); return; }
            execute(() -> exchange(base,"POST","/api/v1/auth/logout",new JSONObject(),token),
                ignored -> { TokenStore.clear(this); form(); });
        });
        Button clear=button("Xóa phiên trên máy",false);
        p.addView(clear,spacing(12));
        clear.setOnClickListener(v -> { TokenStore.clear(this); form(); });
        show(p);
    }
    @Override protected void onDestroy() { workers.shutdownNow(); super.onDestroy(); }
}
