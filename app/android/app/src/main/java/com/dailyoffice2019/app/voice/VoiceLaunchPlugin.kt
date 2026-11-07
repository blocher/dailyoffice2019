package com.dailyoffice2019.app.voice

import androidx.core.content.pm.ShortcutInfoCompat
import androidx.core.content.pm.ShortcutManagerCompat
import androidx.core.graphics.drawable.IconCompat
import com.dailyoffice2019.app.R
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

/**
 * The page tells Android what the listener opens and plays (app/src/helpers/voice.js donateActivity),
 * and each becomes a dynamic shortcut: offered on the launcher icon's long press, ranked by use,
 * and, through its capability binding, something Google Assistant can open by name ("open Compline
 * on Daily Office"). The Android side of ios/App/App/Voice/VoiceLaunchPlugin.swift.
 *
 * Pages open from the shortcuts' dailyoffice2019:// links, which the App plugin passes to the page
 * as appUrlOpen; this plugin has no "open" event of its own on Android.
 */
@CapacitorPlugin(name = "VoiceLaunch")
class VoiceLaunchPlugin : Plugin() {

    @PluginMethod
    fun donate(call: PluginCall) {
        val shortcut = when (call.getString("kind")) {
            "office" -> {
                val office = Office.find(call.getString("serviceType"), call.getString("office"))
                if (office == null) {
                    call.reject("Unknown office")
                    return
                }
                Donation(
                    id = "office-${office.key}",
                    shortLabel = shortLabel(office),
                    longLabel = office.title,
                    path = office.path,
                    // The shortcut plays: someone who comes back by voice or long press wants to pray.
                    autoplay = true,
                    names = listOf(office.title) + office.synonyms,
                )
            }
            "readings" -> {
                val service = ReadingsService.entries.firstOrNull { it.slug == call.getString("service") }
                    ?: ReadingsService.MORNING_PRAYER
                Donation(
                    id = "readings-${service.slug}",
                    shortLabel = "Readings",
                    longLabel = "Readings for ${service.title}",
                    path = service.path,
                    autoplay = call.getBoolean("played", false) == true,
                    names = listOf("Readings for ${service.title}", "Today's readings"),
                )
            }
            "psalm" -> {
                val number = call.getInt("number")
                if (number == null || number !in 1..150) {
                    call.reject("Unknown psalm")
                    return
                }
                Donation("psalm-$number", "Psalm $number", "Psalm $number", "/psalm/$number/", false, listOf("Psalm $number"))
            }
            else -> {
                call.reject("Not something to remember")
                return
            }
        }
        try {
            ShortcutManagerCompat.pushDynamicShortcut(context, shortcut.build())
            call.resolve()
        } catch (error: Exception) {
            // Launchers may refuse (rate limits, work profiles); nothing the listener needs to know.
            call.resolve()
        }
    }

    private fun shortLabel(office: Office): String = when (office) {
        Office.FAMILY_MORNING -> "Family Morning"
        Office.FAMILY_MIDDAY -> "Family Midday"
        Office.FAMILY_EARLY_EVENING -> "Family Evening"
        Office.FAMILY_CLOSE_OF_DAY -> "Close of Day"
        else -> office.title
    }

    private inner class Donation(
        val id: String,
        val shortLabel: String,
        val longLabel: String,
        val path: String,
        val autoplay: Boolean,
        val names: List<String>,
    ) {
        fun build(): ShortcutInfoCompat =
            ShortcutInfoCompat.Builder(context, id)
                .setShortLabel(shortLabel)
                .setLongLabel(longLabel)
                .setIcon(IconCompat.createWithResource(context, R.mipmap.ic_launcher))
                .setIntent(VoiceLinks.intent(context, path, autoplay))
                .addCapabilityBinding("actions.intent.OPEN_APP_FEATURE", "feature", names)
                .build()
    }
}
