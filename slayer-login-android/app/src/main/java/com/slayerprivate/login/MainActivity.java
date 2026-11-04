package com.slayerprivate.login;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.util.Base64;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Locale;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * Standalone OFFLINE account UI proof of concept.
 *
 * Does NOT log into the original Slayer Legend game.
 * Does NOT implement a backend, OAuth, or LIAPP bypass.
 * Credentials are stored locally as salted PBKDF2 hashes.
 */
public final class MainActivity extends Activity {
    private static final int BG = Color.rgb(12, 17, 30);
    private static final int PANEL = Color.rgb(23, 31, 48);
    private static final int GOLD = Color.rgb(255, 204, 108);
    private static final int WHITE = Color.rgb(242, 245, 251);
    private static final int MUTED = Color.rgb(160, 172, 195);
    private static final int ROUNDS = 180000;

    private SharedPreferences prefs;
    private boolean creating = false;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("slayer_local_accounts_v1", MODE_PRIVATE);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        showForm();
    }

    private int dp(float value) {
        return (int) (getResources().getDisplayMetrics().density * value + 0.5f);
    }

    private GradientDrawable background(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radius));
        return drawable;
    }

    private TextView text(String content, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(content);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(null, Typeface.BOLD);
        return view;
    }

    private LinearLayout.LayoutParams layoutParams(int top) {
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT);
        params.topMargin = dp(top);
        return params;
    }

    private EditText entry(String hint, boolean secret) {
        EditText edit = new EditText(this);
        edit.setSingleLine(true);
        edit.setTextColor(WHITE);
        edit.setHintTextColor(MUTED);
        edit.setHint(hint);
        edit.setTextSize(16f);
        edit.setPadding(dp(16), dp(10), dp(16), dp(10));
        edit.setBackground(background(PANEL, 12));
        if (secret) {
            edit.setInputType(InputType.TYPE_CLASS_TEXT |
                    InputType.TYPE_TEXT_VARIATION_PASSWORD);
        } else {
            edit.setInputType(InputType.TYPE_CLASS_TEXT |
                    InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        }
        return edit;
    }

    private Button button(String title, boolean primary) {
        Button button = new Button(this);
        button.setText(title);
        button.setAllCaps(false);
        button.setTextSize(16f);
        button.setTypeface(null, Typeface.BOLD);
        button.setTextColor(primary ? BG : WHITE);
        button.setBackground(background(primary ? GOLD : PANEL, 12));
        button.setMinHeight(dp(50));
        return button;
    }

    private LinearLayout page() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(24), dp(54), dp(24), dp(36));
        page.setBackgroundColor(BG);
        return page;
    }

    private void showPage(LinearLayout page) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setFitsSystemWindows(true);
        scroll.setBackgroundColor(BG);
        scroll.addView(page);
        setContentView(scroll);
    }

    private static String normalize(String username) {
        return username.trim().toLowerCase(Locale.ROOT);
    }

    private static byte[] derive(char[] password, byte[] salt) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(password, salt, ROUNDS, 256);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                    .generateSecret(spec).getEncoded();
        } finally {
            spec.clearPassword();
        }
    }

    private static String b64(byte[] value) {
        return Base64.encodeToString(value, Base64.NO_WRAP);
    }

    private static byte[] unb64(String value) {
        return Base64.decode(value, Base64.NO_WRAP);
    }

    private void showForm() {
        LinearLayout page = page();

        TextView emblem = text("✦  SLAYER LOGIN", 14, GOLD, true);
        emblem.setGravity(Gravity.CENTER_HORIZONTAL);
        page.addView(emblem);

        TextView header = text(
                creating ? "Tạo tài khoản" : "Chào mừng trở lại", 28, WHITE, true);
        header.setGravity(Gravity.CENTER_HORIZONTAL);
        page.addView(header, layoutParams(28));

        TextView notice = text("Bản đăng nhập thử nghiệm • Chạy offline",
                13, MUTED, false);
        notice.setGravity(Gravity.CENTER_HORIZONTAL);
        page.addView(notice, layoutParams(12));

        EditText username = entry("Tên tài khoản", false);
        page.addView(username, layoutParams(42));

        EditText password = entry("Mật khẩu", true);
        page.addView(password, layoutParams(12));

        TextView status = text("", 14, GOLD, false);
        page.addView(status, layoutParams(14));

        Button action = button(creating ? "Đăng ký" : "Đăng nhập", true);
        page.addView(action, layoutParams(12));

        Button other = button(
                creating ? "Đã có tài khoản? Đăng nhập"
                         : "Chưa có tài khoản? Đăng ký", false);
        page.addView(other, layoutParams(12));
        Button online = button("ĐĂNG NHẬP SERVER (V2)", false);
        page.addView(online, layoutParams(16));
        online.setOnClickListener(v -> startActivity(
                new Intent(this, RemoteAuthActivity.class)));

        TextView warning = text(
                "Tài khoản chỉ lưu trên điện thoại này. " +
                "Không kết nối máy chủ hoặc game Slayer Legend gốc.",
                12, MUTED, false);
        warning.setGravity(Gravity.CENTER_HORIZONTAL);
        page.addView(warning, layoutParams(38));

        action.setOnClickListener(v -> {
            String name = normalize(username.getText().toString());
            char[] pass = password.getText().toString().toCharArray();
            password.setText("");

            try {
                if (!name.matches("[a-z0-9_]{3,24}") || pass.length < 8) {
                    status.setText("Tên 3–24 ký tự; mật khẩu ít nhất 8 ký tự.");
                    return;
                }
                if (creating) {
                    register(name, pass, status);
                } else {
                    logIn(name, pass, status);
                }
            } catch (Exception e) {
                status.setText("Không xử lý được tài khoản trên thiết bị.");
            } finally {
                Arrays.fill(pass, '\0');
            }
        });

        other.setOnClickListener(v -> {
            creating = !creating;
            showForm();
        });

        showPage(page);
    }

    private void register(String name, char[] pass, TextView status)
            throws Exception {
        String key = "user:" + name;
        if (prefs.contains(key)) {
            status.setText("Tên tài khoản đã tồn tại.");
            return;
        }

        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        byte[] hash = derive(pass, salt);
        String stored = b64(salt) + ":" + b64(hash);
        Arrays.fill(hash, (byte) 0);

        if (!prefs.edit().putString(key, stored).commit()) {
            status.setText("Không lưu được tài khoản.");
            return;
        }

        creating = false;
        showForm();
        android.widget.Toast.makeText(
                this, "Đăng ký thành công, hãy đăng nhập",
                android.widget.Toast.LENGTH_LONG).show();
    }

    private void logIn(String name, char[] pass, TextView status)
            throws Exception {
        String record = prefs.getString("user:" + name, null);
        if (record == null) {
            status.setText("Sai tài khoản hoặc mật khẩu.");
            return;
        }

        String[] parts = record.split(":", -1);
        if (parts.length != 2) {
            status.setText("Dữ liệu tài khoản không hợp lệ.");
            return;
        }

        byte[] salt = unb64(parts[0]);
        byte[] saved = unb64(parts[1]);

        if (salt.length != 16 || saved.length != 32) {
            status.setText("Dữ liệu tài khoản không hợp lệ.");
            return;
        }

        byte[] candidate = derive(pass, salt);
        boolean matched = MessageDigest.isEqual(saved, candidate);
        Arrays.fill(candidate, (byte) 0);
        Arrays.fill(saved, (byte) 0);

        if (matched) {
            showHome(name);
        } else {
            status.setText("Sai tài khoản hoặc mật khẩu.");
        }
    }

    private void showHome(String name) {
        LinearLayout page = page();
        page.addView(text("✦  ĐĂNG NHẬP THÀNH CÔNG", 16, GOLD, true));
        page.addView(text("Xin chào, " + name, 26, WHITE, true),
                layoutParams(24));
        page.addView(text(
                "Tài khoản local đã được xác minh.\n" +
                "Đây chưa phải bản sửa đổi game gốc.",
                15, MUTED, false), layoutParams(22));

        Button logout = button("Đăng xuất", true);
        page.addView(logout, layoutParams(32));
        logout.setOnClickListener(v -> {
            creating = false;
            showForm();
        });
        showPage(page);
    }
}
