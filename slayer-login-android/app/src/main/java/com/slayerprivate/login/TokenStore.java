package com.slayerprivate.login;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Encrypts the server bearer token using an Android Keystore AES-GCM key. */
public final class TokenStore {
    private static final String ALIAS = "slayer_auth_token_v2";
    private static final String PREFS = "slayer_auth_secrets_v2";
    private TokenStore() {}

    private static SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if (store.containsAlias(ALIAS)) {
            return (SecretKey) store.getKey(ALIAS, null);
        }
        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(
                ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build());
        return generator.generateKey();
    }

    public static void save(Context context, String value) throws Exception {
        if (!value.matches("[a-f0-9]{64}")) {
            throw new IllegalArgumentException("Invalid bearer token");
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        String record = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + ":"
                + Base64.encodeToString(cipher.doFinal(
                        value.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP);
        boolean stored = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString("token", record).commit();
        if (!stored) throw new IllegalStateException("Unable to save token");
    }

    public static String load(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String record = prefs.getString("token", null);
        if (record == null) return null;
        try {
            String[] items = record.split(":", -1);
            if (items.length != 2) throw new IllegalArgumentException("Bad ciphertext");
            byte[] iv = Base64.decode(items[0], Base64.NO_WRAP);
            byte[] value = Base64.decode(items[1], Base64.NO_WRAP);
            if (iv.length != 12) throw new IllegalArgumentException("Bad IV");
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
            String decoded = new String(cipher.doFinal(value), StandardCharsets.UTF_8);
            if (!decoded.matches("[a-f0-9]{64}")) throw new IllegalArgumentException();
            return decoded;
        } catch (Exception e) {
            clear(context);
            return null;
        }
    }

    public static void clear(Context context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().remove("token").commit();
    }
}
