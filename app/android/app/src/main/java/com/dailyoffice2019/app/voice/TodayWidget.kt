package com.dailyoffice2019.app.voice

import android.app.AlarmManager
import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.widget.RemoteViews
import androidx.core.content.edit
import androidx.core.graphics.toColorInt
import com.dailyoffice2019.app.R
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import org.json.JSONObject

/**
 * The day in the church calendar on the home screen: the feast or Sunday, its season and color,
 * the saint remembered, and any fast. After 3 p.m. it shows the evening's observance (the eve of a
 * feast). The Android side of ios/App/DailyOfficeWidget/DailyOfficeWidget.swift.
 *
 * On a plain weekday (a feria) with a saint it names the saint, or the weekday if someone chooses
 * so (TodayWidgetConfigureActivity, from the widget's settings). It reads the calendar API, keeps
 * the last day it read for when there is no network, and reads again at 3 p.m. and just after
 * midnight.
 */
class TodayWidget : AppWidgetProvider() {

    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        refresh(context, ids, goAsync())
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_REFRESH) {
            val ids = widgetIds(context)
            if (ids.isNotEmpty()) refresh(context, ids, goAsync())
        }
    }

    override fun onDeleted(context: Context, ids: IntArray) {
        preferences(context).edit { ids.forEach { remove(saintKey(it)) } }
    }

    companion object {
        private const val ACTION_REFRESH = "com.dailyoffice2019.app.voice.TodayWidget.REFRESH"
        private const val PREFERENCES = "TodayWidget"
        private const val EVENING_HOUR = 15

        private fun preferences(context: Context) = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

        private fun saintKey(id: Int) = "saint_on_weekdays_$id"

        /** Whether this widget names a weekday by its saint (the default) rather than by the weekday. */
        fun showsSaint(context: Context, id: Int): Boolean = preferences(context).getBoolean(saintKey(id), true)

        fun setShowsSaint(context: Context, id: Int, saint: Boolean) {
            preferences(context).edit { putBoolean(saintKey(id), saint) }
        }

        private fun widgetIds(context: Context): IntArray =
            AppWidgetManager.getInstance(context).getAppWidgetIds(ComponentName(context, TodayWidget::class.java))

        /** Reads the day again for every widget, if there are any (the app calls this when it opens). */
        @JvmStatic
        fun refreshAll(context: Context) {
            val ids = widgetIds(context)
            if (ids.isNotEmpty()) refresh(context.applicationContext, ids, null)
        }

        fun refresh(context: Context, ids: IntArray, done: android.content.BroadcastReceiver.PendingResult?) {
            Thread {
                try {
                    val now = Calendar.getInstance()
                    val day = load(context, now)
                    val manager = AppWidgetManager.getInstance(context)
                    for (id in ids) manager.updateAppWidget(id, views(context, id, day, now))
                    scheduleNext(context, now)
                } catch (_: Exception) {
                    // Leave the widget as it was; the next refresh tries again.
                } finally {
                    done?.finish()
                }
            }.start()
        }

        /** Today, from the calendar, or as last read today. */
        private fun load(context: Context, now: Calendar): CalendarDay? {
            val key = "day_${CalendarApi.apiDate(now)}"
            val store = preferences(context)
            return try {
                val obj = CalendarApi.get("calendar/${CalendarApi.apiDate(now)}") as JSONObject
                // Keep only today's; the widgets' choices stay.
                store.edit {
                    store.all.keys.filter { it.startsWith("day_") && it != key }.forEach { remove(it) }
                    putString(key, obj.toString())
                }
                CalendarDay(obj)
            } catch (_: Exception) {
                store.getString(key, null)?.let { CalendarDay(JSONObject(it)) }
            }
        }

        private fun views(context: Context, id: Int, day: CalendarDay?, now: Calendar): RemoteViews {
            val views = RemoteViews(context.packageName, R.layout.widget_today)
            val evening = now.get(Calendar.HOUR_OF_DAY) >= EVENING_HOUR
            val night = (context.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
                Configuration.UI_MODE_NIGHT_YES

            views.setTextViewText(
                R.id.widget_eyebrow,
                "● " + context.getString(if (evening) R.string.widget_this_evening else R.string.widget_today),
            )
            views.setTextViewText(R.id.widget_date, SimpleDateFormat("EEEE, MMMM d", Locale.getDefault()).format(now.time))

            if (day == null) {
                views.setTextViewText(R.id.widget_title, context.getString(R.string.widget_offline))
                views.setTextViewText(R.id.widget_details, "")
            } else {
                val saintFirst = showsSaint(context, id)
                val observance = if (evening) day.primaryEveningFeast.ifEmpty { day.primaryFeast } else day.primaryFeast
                val headline = if (evening) day.eveningHeadline else day.headline
                val title = if (saintFirst) headline else observance
                val shownSaint = if (saintFirst && headline != observance) shortSaint(headline) else null
                val saint = day.saints
                    .filter { shorten(it.name) != shorten(day.primaryFeast) }
                    .map { shortSaint(it.name) }
                    .firstOrNull { it != shownSaint }
                val season = if (day.seasonName.lowercase().startsWith("season")) {
                    day.seasonName.replace("After", "after")
                } else {
                    day.seasonName
                }
                val fast = if (day.fastDay > 0) fastLabel(day.fastDescription) else null
                views.setTextViewText(R.id.widget_title, shorten(title))
                views.setTextViewText(
                    R.id.widget_details,
                    listOfNotNull(season.ifEmpty { null }, saint, fast).joinToString(" · "),
                )
                val accent = seasonColor(if (evening) day.primaryEveningColor else day.primaryColor, night)
                views.setInt(R.id.widget_bar, "setBackgroundColor", accent)
                views.setTextColor(R.id.widget_eyebrow, accent)
                views.setTextColor(R.id.widget_pray, accent)
                views.setTextColor(R.id.widget_readings, accent)
            }

            views.setOnClickPendingIntent(R.id.widget_root, VoiceLinks.pendingIntent(context, "/"))
            // The office for this time of day, ready to pray (not playing).
            views.setOnClickPendingIntent(R.id.widget_pray, VoiceLinks.pendingIntent(context, "/"))
            views.setOnClickPendingIntent(R.id.widget_readings, VoiceLinks.pendingIntent(context, "/readings/"))
            return views
        }

        /** Reads again at 3 p.m., when the evening's observance begins, and just after midnight. */
        private fun scheduleNext(context: Context, now: Calendar) {
            val next = (now.clone() as Calendar).apply {
                if (get(Calendar.HOUR_OF_DAY) < EVENING_HOUR) {
                    set(Calendar.HOUR_OF_DAY, EVENING_HOUR)
                    set(Calendar.MINUTE, 0)
                } else {
                    add(Calendar.DAY_OF_MONTH, 1)
                    set(Calendar.HOUR_OF_DAY, 0)
                    set(Calendar.MINUTE, 5)
                }
                set(Calendar.SECOND, 0)
            }
            val intent = Intent(context, TodayWidget::class.java).setAction(ACTION_REFRESH)
            val pending = PendingIntent.getBroadcast(
                context,
                0,
                intent,
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
            )
            // Inexact is fine: a few minutes late is still the right day.
            context.getSystemService(AlarmManager::class.java)?.set(AlarmManager.RTC, next.timeInMillis, pending)
        }

        /**
         * "Tuesday after the Twenty-third Sunday after Pentecost, or the Twenty-second Sunday after
         * Trinity (Proper 26)" -> "Tuesday after the Twenty-third Sunday after Pentecost".
         */
        fun shorten(name: String): String =
            name.substringBefore(", or the ").replace(Regex("\\s*\\(Proper \\d+\\)"), "").trim()

        /** "Willibrord, Archbishop of Utrecht and Missionary to Frisia, 739" -> "Willibrord". */
        fun shortSaint(name: String): String = name.substringBefore(",").trim()

        /** "Fast (Total abstinence)" -> "Fast · total abstinence". */
        fun fastLabel(description: String): String {
            val open = description.indexOf('(')
            val close = description.lastIndexOf(')')
            if (open in 0 until close) return "Fast · " + description.substring(open + 1, close).lowercase()
            return description.ifEmpty { "Fast day" }
        }

        /** The app's season colors (app/src/styles/tokens.css), light and dark. */
        fun seasonColor(name: String, night: Boolean): Int {
            val (light, dark) = when (name.lowercase()) {
                "red" -> "#A8241C" to "#E4776D"
                "green" -> "#2F6A3B" to "#82BF8F"
                "purple", "violet", "lenten array" -> "#5B2B84" to "#BB9CDB"
                "white", "gold" -> "#9A7A22" to "#DCBC66"
                "black" -> "#3A3733" to "#AAA298"
                "rose" -> "#A94A76" to "#E59ABA"
                "blue" -> "#2A4D97" to "#93B2EC"
                else -> "#8A2C25" to "#DF8A7C"
            }
            return (if (night) dark else light).toColorInt()
        }
    }
}
