package com.philmerrell.firebaseanalytics;

import android.Manifest;
import android.content.Context;
import android.os.Bundle;
import android.util.Log;

import com.getcapacitor.JSObject;
import com.getcapacitor.NativePlugin;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.cordova.MockCordovaWebViewImpl;
import com.google.firebase.analytics.FirebaseAnalytics;
import org.json.JSONException;
import org.json.JSONObject;
import java.util.Iterator;

@NativePlugin(
    permissions = {
        Manifest.permission.ACCESS_NETWORK_STATE,
        Manifest.permission.INTERNET,
        Manifest.permission.WAKE_LOCK
    }
)
public class CapacitorFirebaseAnalytics extends Plugin {

    private FirebaseAnalytics firebaseAnalytics;

    public void load() {
        firebaseAnalytics = FirebaseAnalytics.getInstance(getContext());
    }

    @PluginMethod()
    public void setUserProperty(PluginCall call) throws JSONException {
        try {
            final String name = call.getString("name");
            final String value = call.getString("value");
            if (name != null && value != null) {
                firebaseAnalytics.setUserProperty(name, value);
                call.success();
            } else {
                call.reject("key 'name' or 'value' does not exist");
            }
        } catch (Exception e) {
            call.reject(e.getLocalizedMessage(), e);
        }
    }

    @PluginMethod()
    public void logEvent(PluginCall call) {
        try {
            final String name = call.getString("name", null);
            JSObject data = call.getData();
            final JSONObject params = data.optJSONObject("parameters");
            if (name != null) {
                Bundle bundle = new Bundle();

                if (params != null) {
                    Iterator<String> keys = params.keys();

                    while (keys.hasNext()) {
                        String key = keys.next();
                        Object value = params.get(key);

                        if (value instanceof String) {
                            bundle.putString(key, (String) value);
                        } else if (value instanceof Integer) {
                            bundle.putInt(key, (Integer) value);
                        } else if (value instanceof Double) {
                            bundle.putDouble(key, (Double) value);
                        } else if (value instanceof Long) {
                            bundle.putLong(key, (Long) value);
                        } else {
                            call.reject("Value for key " + key + " not one of (String, Integer, Double, Long)");
                        }
                    }
                } else {
                    call.reject("key 'parameters' does not exist");
                }
                firebaseAnalytics.logEvent(name, bundle);
                call.success();
            } else {
                call.reject("key 'name' does not exist");
            }
        } catch (Exception e) {
            call.reject(e.getLocalizedMessage(), e);
        }
    }

    @PluginMethod()
    public void setUserId(PluginCall call) {
        try {
            final String userId = call.getString("userId");
            if (userId != null) {
                firebaseAnalytics.setUserId(userId);
                call.success();
            } else {
                call.reject("key 'userId' does not exist");
            }
        } catch (Exception e) {
            call.reject(e.getLocalizedMessage(), e);
        }
    }

    @PluginMethod()
    public void setScreenName(PluginCall call) {
        try {
            final String value = call.getString("screenName");
            final String overrideName = call.getString("screenClassOverride", null);
            getActivity().runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    firebaseAnalytics.setCurrentScreen(getActivity(), value, overrideName);
                }
            });
            call.success();
        } catch (Exception e) {
            call.reject(e.getLocalizedMessage(), e);
        }
    }

    @PluginMethod()
    public void appInstanceId(PluginCall call) {
        try {
            String appId = firebaseAnalytics.getAppInstanceId().toString();
            JSObject ret = new JSObject();
            ret.put("appId", appId);
            call.success(ret);
        } catch (Exception e) {
            call.reject(e.getLocalizedMessage(), e);
        }
    }

    @PluginMethod()
    public void resetAnalyticsData(PluginCall call) {
        try {
            firebaseAnalytics.resetAnalyticsData();
            call.success();
        } catch (Exception e) {
            call.reject(e.getLocalizedMessage(), e);
        }
    }
}
