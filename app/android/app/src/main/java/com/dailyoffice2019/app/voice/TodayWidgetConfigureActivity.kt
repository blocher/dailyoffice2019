package com.dailyoffice2019.app.voice

import android.app.Activity
import android.app.AlertDialog
import android.appwidget.AppWidgetManager
import android.content.Intent
import android.content.res.Configuration
import android.os.Bundle
import com.dailyoffice2019.app.R

/**
 * The calendar widget's one setting: on a plain weekday with a saint, show the saint (the default)
 * or the weekday. Opened from the widget's settings; on Android 11 and earlier, also when the
 * widget is added.
 */
class TodayWidgetConfigureActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val id = intent.extras?.getInt(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
            ?: AppWidgetManager.INVALID_APPWIDGET_ID
        val result = Intent().putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, id)
        setResult(RESULT_CANCELED, result)
        if (id == AppWidgetManager.INVALID_APPWIDGET_ID) {
            finish()
            return
        }

        val night = (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
            Configuration.UI_MODE_NIGHT_YES
        val theme = if (night) {
            android.R.style.Theme_DeviceDefault_Dialog_Alert
        } else {
            android.R.style.Theme_DeviceDefault_Light_Dialog_Alert
        }
        val choices = arrayOf(getString(R.string.widget_weekday_saint), getString(R.string.widget_weekday_weekday))
        AlertDialog.Builder(this, theme)
            .setTitle(R.string.widget_weekday_title)
            .setSingleChoiceItems(choices, if (TodayWidget.showsSaint(this, id)) 0 else 1) { dialog, which ->
                TodayWidget.setShowsSaint(this, id, which == 0)
                TodayWidget.refresh(applicationContext, intArrayOf(id), null)
                setResult(RESULT_OK, result)
                dialog.dismiss()
            }
            .setOnCancelListener {
                // Keeping the current choice still completes setup when the widget is added.
                setResult(RESULT_OK, result)
                TodayWidget.refresh(applicationContext, intArrayOf(id), null)
            }
            .setOnDismissListener { finish() }
            .show()
    }
}
