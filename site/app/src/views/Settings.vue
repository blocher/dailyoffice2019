<template>
  <div class="home">
    <h1>Settings</h1>
    <main class="max-w-lg mx-auto pt-10 pb-12 px-4 lg:pb-16">
      <form>
        <RadioGroup v-model="selected" v-bind:key="setting.uuid" v-for="setting in settings">
          <RadioGroupLabel class="text-sm font-medium text-gray-900">
            Privacy
          </RadioGroupLabel>

          <div class="mt-1 bg-white rounded-md shadow-sm -space-y-px">
            <RadioGroupOption as="template" v-for="(option, optionIdx) in setting.options" v-bind:key="option.uuid"
                              :value="option" v-slot="{ checked, active }">
              <div
                  :class="[optionIdx === 0 ? 'rounded-tl-md rounded-tr-md' : '', optionIdx === settings.length - 1 ? 'rounded-bl-md rounded-br-md' : '', checked ? 'bg-sky-50 border-sky-200 z-10' : 'border-gray-200', 'relative border p-4 flex cursor-pointer focus:outline-none']">
                <span
                    :class="[checked ? 'bg-sky-600 border-transparent' : 'bg-white border-gray-300', active ? 'ring-2 ring-offset-2 ring-sky-500' : '', 'h-4 w-4 mt-0.5 cursor-pointer rounded-full border flex items-center justify-center']"
                    aria-hidden="true">
                  <span class="rounded-full bg-white w-1.5 h-1.5"/>
                </span>
                <div class="ml-3 flex flex-col">
                  <RadioGroupLabel as="span"
                                   :class="[checked ? 'text-sky-900' : 'text-gray-900', 'block text-sm font-medium']">
                    A{{ option.name }}B
                  </RadioGroupLabel>
                  <RadioGroupDescription as="span"
                                         :class="[checked ? 'text-sky-700' : 'text-gray-500', 'block text-sm']">
                    C{{ option.description }}D
                  </RadioGroupDescription>
                </div>
              </div>
            </RadioGroupOption>
          </div>
        </RadioGroup>
      </form>
    </main>
  </div>
</template>

<script>
// @ is an alias to /src

import {ref} from 'vue'
import {
  RadioGroup,
  RadioGroupDescription,
  RadioGroupLabel,
  RadioGroupOption,
} from '@headlessui/vue'

const settings = [
  {
    "uuid": "2c630c05-57f0-4cb1-b38d-0ccb985415c7",
    "name": "psalter",
    "title": "Psalter Cycle",
    "description": "During Morning and Evening Prayer, pray through all the Psalms either every <strong>60 days</strong> (fewer psalms per day) or once every <strong>30 days</strong> (more psalms per day).",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 0,
    "options": [
      {
        "uuid": "cdfe15da-b170-4998-a643-a6dc8e0b1ecd",
        "name": "60 Day",
        "description": "Pray through the psalms once every 60 days",
        "value": "60",
        "order": 0
      },
      {
        "uuid": "e49f4448-e583-467e-8773-6a0ea41275a1",
        "name": "30 Day",
        "description": "Pray through the psalms once every 30 days",
        "value": "30",
        "order": 1
      }
    ]
  },
  {
    "uuid": "2777da0f-7363-4896-a018-b2847f6f963b",
    "name": "reading_cycle",
    "title": "Reading Cycle",
    "description": "Read through most of the Bible during Morning and Evening Prayer every <strong>1 year</strong> or every <strong>2 years</strong>.  The one year cycle is best if you do <strong>both</strong> Morning and Evening prayer daily; the two year cycle is best if you do only one.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 1,
    "options": [
      {
        "uuid": "1d06993e-b70c-4cad-91d2-1c5ef6ba9944",
        "name": "One Year",
        "description": "Read through most of the Bible each year. (Use if you pray <strong>both</strong> Morning and Evening Prayer)",
        "value": "1",
        "order": 0
      },
      {
        "uuid": "10c91985-5121-4bf8-8725-c6abadfb6003",
        "name": "Two Year",
        "description": "Read through most of the Bible in two years. (Use if you pray <strong>either</strong> Morning <strong>or</strong> Evening prayer)",
        "value": "2",
        "order": 1
      }
    ]
  },
  {
    "uuid": "b851eec9-f0f5-4749-bbad-e56324e60eb1",
    "name": "reading_length",
    "title": "Reading Length",
    "description": "Always use the full readings, or use the shortened readings (when there are suggested abbreviations).",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 2,
    "options": [
      {
        "uuid": "eea3ec6e-cff9-4c0c-b770-b3da1624d9ed",
        "name": "Full",
        "description": "The full readings will always be used.",
        "value": "full",
        "order": 0
      },
      {
        "uuid": "4565f90a-629e-46d9-99f6-547aa3efebea",
        "name": "Abbreviated",
        "description": "Suggested abbreviations, when available.",
        "value": "abbreviated",
        "order": 1
      }
    ]
  },
  {
    "uuid": "cb8c5f35-4dee-468e-bd99-1aff278381e9",
    "name": "reading_audio",
    "title": "Reading Audio",
    "description": "Show or hide an audio player to listen to the scripture readings during Morning and Evening Prayer.  Audio is provided by esv.org and currently does not include the Deuterocanon/Apocrypha.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 3,
    "options": [
      {
        "uuid": "58121e91-144b-411c-8ba9-b3381aadcc59",
        "name": "Disable Audio",
        "description": "No audio controls for scripture readings",
        "value": "off",
        "order": 0
      },
      {
        "uuid": "18f75361-ea1d-4b1c-ba14-98f5d6cc0dad",
        "name": "Enable Audio",
        "description": "Enable audio player for scripture readings",
        "value": "on",
        "order": 1
      }
    ]
  },
  {
    "uuid": "7fa1ff65-3cef-4f76-8717-160088a523b5",
    "name": "canticle_rotation",
    "title": "Canticle Rotation",
    "description": "",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 4,
    "options": [
      {
        "uuid": "cca2b9b4-0566-4d8e-966e-7360c43c3d1f",
        "name": "Traditional",
        "description": "The traditional fixed canticles each day",
        "value": "default",
        "order": 0
      },
      {
        "uuid": "2a49cf14-3177-40f0-869a-bd9988bdac4d",
        "name": "Seasonal Rotation",
        "description": "One fixed canticle and one canticle that rotates by season",
        "value": "2011",
        "order": 1
      },
      {
        "uuid": "5cc659d9-311d-466b-a209-87feb1cf9ffb",
        "name": "Daily Rotation",
        "description": "A rotating set of canticles by day of week and season",
        "value": "1979",
        "order": 2
      }
    ]
  },
  {
    "uuid": "d682be62-ef62-4e6a-979d-33dc118f10d0",
    "name": "theme",
    "title": "Visual Theme",
    "description": "Use light mode or dark mode, or default to your computer's setting for light or dark mode",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 0,
    "options": [
      {
        "uuid": "85615ecf-8e99-44e7-9132-f1ad1287606c",
        "name": "Use Computer Setting",
        "description": "The long form of the intro and absolution are used every day",
        "value": "theme-auto",
        "order": 0
      },
      {
        "uuid": "4fde2bf5-0e3f-422e-9c2e-149e96577bb2",
        "name": "Light Mode",
        "description": "The long form of the intro and absolution are used only on fast days",
        "value": "theme-light",
        "order": 1
      },
      {
        "uuid": "23ae311c-d217-4110-8c2b-82c9f7541dee",
        "name": "Dark Mode",
        "description": "The short form of the intro and absolution are used every day",
        "value": "theme-dark",
        "order": 2
      }
    ]
  },
  {
    "uuid": "b75c8a15-b58a-4e08-868b-e3357144b922",
    "name": "lectionary",
    "title": "Substitute Sunday/Holy Day (Eucharistic) Lectionary",
    "description": "On Sundays and major holy days, do you want to use the standard Daily Office readings or substitute the 3-year Sunday/Holy Day cycle? When the Daily Office is used for the principal service of a church, the prayer book instructs you to replace the Daily Office readings with the three year cycle of Sunday and Holy Day readings.  This is generally done only in churches and not when using the Daily Office as a personal devotion at home.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 1,
    "options": [
      {
        "uuid": "1b5a302a-d548-4865-a1be-6652948c9616",
        "name": "Standard Daily Office",
        "description": "",
        "value": "daily-office-readings",
        "order": 0
      },
      {
        "uuid": "294176db-3ac3-4012-ae62-5e592b76ee6c",
        "name": "Sundays & Holy Days",
        "description": "",
        "value": "mass-readings",
        "order": 1
      }
    ]
  },
  {
    "uuid": "176d7e5a-408b-4ae3-ba74-a97a29674af5",
    "name": "confession",
    "title": "Confession Intro Length",
    "description": "Use either the short or long exhortation before the confession.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 2,
    "options": [
      {
        "uuid": "81371d0f-7859-4192-904e-7ce96f5c50ac",
        "name": "Long Intro Only on Fast Days",
        "description": "The long form of the intro and absolution are used only on fast days",
        "value": "long-on-fast",
        "order": 0
      },
      {
        "uuid": "ba8ada72-64a9-4557-ac89-bb0f4cbb2af5",
        "name": "Short Intro Always",
        "description": "The short form of the intro and absolution are used every day",
        "value": "short",
        "order": 1
      },
      {
        "uuid": "1a949eee-78f7-4daf-8acf-972d0c2423a0",
        "name": "Long Intro Always",
        "description": "The long form of the intro and absolution are used every day",
        "value": "long",
        "order": 2
      }
    ]
  },
  {
    "uuid": "943d91f2-b6ce-48fe-be16-2ed27d54f722",
    "name": "absolution",
    "title": "Absolution Style",
    "description": "After the confession, read an absolution suitable for a priest or a prayer suitable for a deacon or lay person.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 3,
    "options": [
      {
        "uuid": "a32a1fe6-c1e1-41de-ab78-4a253e601d7b",
        "name": "Deacon or Lay Person",
        "description": "A prayer suitable for a deacon or lay person to read",
        "value": "lay",
        "order": 0
      },
      {
        "uuid": "ca59e832-b049-4fe8-beaa-d4c1959059f9",
        "name": "Priest or Bishop",
        "description": "An absolution suitable for a priest to pronounce",
        "value": "priest",
        "order": 1
      }
    ]
  },
  {
    "uuid": "8919b8b5-b54e-4aa0-b7b6-671ff8c94b0d",
    "name": "morning_prayer_invitatory",
    "title": "Morning Prayer Invitatory",
    "description": "Open with the Venite (Psalm 95) always (traditional), have a special celebratory invitatory on Sundays and feasts (Pascha Nostrum during Eastertide or Jubilate/Psalm 100 otherwise), or rotate between the normal and celebratory invitatory each day. Regardless of which setting you choose, the Pascha Nostrum is always used during the first week of Easter, and the invitatory will never be the same as one of the day's appointed psalms.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 4,
    "options": [
      {
        "uuid": "26cddf46-ae0a-4a22-8f44-7f4828427051",
        "name": "Venite always",
        "description": "Always use the Venite (except on days when Pslam 95 is appointed)",
        "value": "invitatory_traditional",
        "order": 0
      },
      {
        "uuid": "2b5af968-81b2-4135-a5f8-1bf7a8746a07",
        "name": "Celebratory Sundays and feasts",
        "description": "Use the Jubilate on Feasts and Sundays, Venite on other days ",
        "value": "invitatory_jubilate_on_feasts",
        "order": 1
      },
      {
        "uuid": "2ec5e933-a8d5-46ca-877b-be72d5201c08",
        "name": "Rotating each day",
        "description": "Rotate between the Venite and Jubilate",
        "value": "invitatory_rotating",
        "order": 2
      },
      {
        "uuid": "2534f06e-bd45-46fe-9829-ace751e9bdbd",
        "name": "Celebratory Always",
        "description": "Always use the Jubilate (or Pascha Nostrum, in Eastertide)",
        "value": "celebratory_always",
        "order": 3
      }
    ]
  },
  {
    "uuid": "13d12ab5-d4f3-4878-af54-e2e4bc328029",
    "name": "reading_headings",
    "title": "Reading Headings",
    "description": "Show or hide headings from the English Standard Version of the Bible in scripture readings ",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 5,
    "options": [
      {
        "uuid": "c20ff1a0-b498-4ef8-800f-864fc7934b06",
        "name": "Hide",
        "description": "Hide ESV headings in readings",
        "value": "off",
        "order": 0
      },
      {
        "uuid": "549a0723-ed28-4572-8dee-d4156b2b0570",
        "name": "Show",
        "description": "Show ESV headings in readings",
        "value": "on",
        "order": 1
      }
    ]
  },
  {
    "uuid": "2bf5d7b8-1a4d-4b82-a60b-ecb307aad3dd",
    "name": "language_style",
    "title": "Language Style for Prayers",
    "description": "Traditional and contemporary language options are available for the Kyrie (Lord have mercy) and the Lord's Prayer",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 6,
    "options": [
      {
        "uuid": "2e4c71de-45f1-4fa6-92a1-cd25a81d22a5",
        "name": "Traditional",
        "description": "Traditional language for the Kyrie and Our Father",
        "value": "traditional",
        "order": 0
      },
      {
        "uuid": "1c75c19a-cae7-4bd4-81fc-6f8918c1f628",
        "name": "Contemporary",
        "description": "Modern language for the Kyrie and Our Father",
        "value": "contemporary",
        "order": 1
      }
    ]
  },
  {
    "uuid": "4b9dcea1-8a1c-4d21-addb-1535b286efcd",
    "name": "national_holidays",
    "title": "National Holiday Collects",
    "description": "Show country-specific commemorations for the United States, Canada, or both.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 7,
    "options": [
      {
        "uuid": "51474eed-803b-4c78-837e-0ae1d7bd430d",
        "name": "All",
        "description": "Both U.S. and Canadian Holidays",
        "value": "all",
        "order": 0
      },
      {
        "uuid": "fcb9589e-254f-48a1-a242-7401fc8fa100",
        "name": "United States",
        "description": "United States Holidays",
        "value": "us",
        "order": 1
      },
      {
        "uuid": "8547a67c-7abe-4da4-bf09-cc577ad85791",
        "name": "Canada",
        "description": "Canadian Holidays",
        "value": "canada",
        "order": 2
      },
      {
        "uuid": "eb249d16-abbb-4684-a1c6-3e6e7bca9063",
        "name": "None",
        "description": "No Holidays",
        "value": "national_none",
        "order": 3
      }
    ]
  },
  {
    "uuid": "144454e3-6759-43b3-9654-b380eef228f6",
    "name": "suffrages",
    "title": "Evening Prayer Suffrages",
    "description": "Choose which set of short prayers to be used each evening",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 8,
    "options": [
      {
        "uuid": "14062a93-17a3-435e-9e4a-ba036c853608",
        "name": "Rotating",
        "description": "Rotate between the traditional and new set each day",
        "value": "rotating",
        "order": 0
      },
      {
        "uuid": "ea76d9a7-4123-4052-9b9f-fe6b999cce98",
        "name": "Traditional",
        "description": "Always use the traditional set (same as Morning Prayer)",
        "value": "traditional",
        "order": 1
      },
      {
        "uuid": "116123c5-1005-4134-8d00-209d93bc81cf",
        "name": "New",
        "description": "Always use the newer set, each ending with \"We entreat you, O Lord\"",
        "value": "new",
        "order": 2
      }
    ]
  },
  {
    "uuid": "b75b26d3-ce37-42e6-a95c-537ec7d81c74",
    "name": "collects",
    "title": "Additional Collects",
    "description": "Use a different collect for each day of the week, or use the same two collects (from the classic prayer books) each day.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 9,
    "options": [
      {
        "uuid": "4d831b0f-4063-4fe0-838b-663740511125",
        "name": "Rotating",
        "description": "A different collect is said for each day of the week",
        "value": "rotating",
        "order": 0
      },
      {
        "uuid": "f2f12c1b-177b-4588-8a0c-f39c276385d9",
        "name": "Fixed",
        "description": "The two traditional collects are said every day",
        "value": "fixed",
        "order": 1
      }
    ]
  },
  {
    "uuid": "f78aff39-9c55-49a3-ae2f-68ee622d92cb",
    "name": "election_prayers",
    "title": "Prayers in the Time of An Election",
    "description": "Include election related collects until the U.S. General election. (Automatically disabled if only Canadian feasts are selected).",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 10,
    "options": [
      {
        "uuid": "e94d73f1-044a-4c2a-84e0-818d30a00735",
        "name": "On",
        "description": "election_yes",
        "value": "election_yes",
        "order": 0
      },
      {
        "uuid": "96f62de6-34bb-479f-aa67-3bf9aed11c91",
        "name": "Off",
        "description": "election_no",
        "value": "election_no",
        "order": 1
      }
    ]
  },
  {
    "uuid": "be27394c-8618-46d1-8384-6c05504dfca6",
    "name": "pandemic_prayers",
    "title": "Prayers in the Time of Pandemic",
    "description": "Include a rotating set of collects for the duration of this pandemic",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 11,
    "options": [
      {
        "uuid": "12aee68f-154c-4a36-8df2-a2e1f6871bed",
        "name": "On",
        "description": "pandemic_yes",
        "value": "pandemic_yes",
        "order": 0
      },
      {
        "uuid": "d542f96a-8eaa-4ce2-9feb-fa45f9d13479",
        "name": "Off",
        "description": "pandemic_no",
        "value": "pandemic_no",
        "order": 1
      }
    ]
  },
  {
    "uuid": "b215f241-7aed-49f5-b901-0a73edc1822c",
    "name": "mp_great_litany",
    "title": "Great Litany at Morning Prayer",
    "description": "Include the Great Litany after the collects at Morning Prayer",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 12,
    "options": [
      {
        "uuid": "f31ff510-e6bd-4c52-8b3e-307122ba7be6",
        "name": "Off",
        "description": "Do not use the litany",
        "value": "mp_litany_off",
        "order": 0
      },
      {
        "uuid": "97a6254b-1078-46a5-8a3a-a005fb854b59",
        "name": "Wed, Fri, & Sun.",
        "description": "Litany on Wednesday, Friday, and Sunday (the traditional days)",
        "value": "mp_litany_w_f_s",
        "order": 1
      },
      {
        "uuid": "7565b132-5d47-4543-b207-6f727ce67d14",
        "name": "Everyday",
        "description": "Litany every day",
        "value": "mp_litany_everyday",
        "order": 2
      }
    ]
  },
  {
    "uuid": "c108186f-ef8d-4add-a2e4-03270e632588",
    "name": "ep_great_litany",
    "title": "Great Litany at Evening Prayer",
    "description": "Include the Great Litany after the collects at Evening Prayer",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 13,
    "options": [
      {
        "uuid": "f8e46995-5fed-4ac7-ad15-98878c1ddf30",
        "name": "Off",
        "description": "Do not use the litany",
        "value": "ep_litany_off",
        "order": 0
      },
      {
        "uuid": "c021a4c6-1964-4740-be8d-0e6f1faa46c1",
        "name": "Wed, Fri, & Sun.",
        "description": "Litany on Wednesday, Friday, and Sunday (the traditional days)",
        "value": "ep_litany_w_f_s",
        "order": 1
      },
      {
        "uuid": "65ab8c99-302c-4edd-81a2-d7c07d03894e",
        "name": "Everyday",
        "description": "Litany every day",
        "value": "ep_litany_everyday",
        "order": 2
      }
    ]
  },
  {
    "uuid": "4534a31d-c5ab-4b88-ae25-9005303fdba9",
    "name": "general_thanksgiving",
    "title": "General Thanksgiving",
    "description": "Pray the General Thanksgiving at the end of Morning and Evening Prayer",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 14,
    "options": [
      {
        "uuid": "1703477b-85cd-45bc-bab2-7187cfa3f791",
        "name": "On",
        "description": "Add the prayer of general thanksgiving at the end of the office",
        "value": "on",
        "order": 0
      },
      {
        "uuid": "4f074ac6-681e-4782-a133-447580aaff32",
        "name": "Off",
        "description": "Hide the prayer of general thanksgiving at the end of the office",
        "value": "off",
        "order": 1
      }
    ]
  },
  {
    "uuid": "7e57f57b-2e57-45ae-8f3b-f51edbdf41f2",
    "name": "chrysostom",
    "title": "Prayer of St. John Chrysostom",
    "description": "Pray the Prayer of St. John Chrysostom at the end of Morning and Evening Prayer.  This prayer is suitable when praying in a group.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 15,
    "options": [
      {
        "uuid": "d3201e43-3cf7-4736-8b2e-8351b221e7d3",
        "name": "On",
        "description": "For use when praying in groups of two or more",
        "value": "on",
        "order": 0
      },
      {
        "uuid": "ae2aa5d1-0b31-4a0d-abf7-417be3fa1979",
        "name": "Off",
        "description": "For when praying individually",
        "value": "off",
        "order": 1
      }
    ]
  },
  {
    "uuid": "de3be90c-2a2b-4927-9af4-20e67cfa1ebf",
    "name": "grace",
    "title": "The Grace",
    "description": "Rotate each day through the three provided conclusions, or always use the same one from the classic prayer books.",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 16,
    "options": [
      {
        "uuid": "7a6612bd-a981-4ced-8c78-98288c457cb6",
        "name": "Rotating",
        "description": "Rotate through three different verses daily",
        "value": "rotating",
        "order": 0
      },
      {
        "uuid": "f36d678d-f2bf-44ff-8d26-f154c0f098d5",
        "name": "Traditional",
        "description": "Conclude with the traditional grace each day",
        "value": "traditional",
        "order": 1
      }
    ]
  },
  {
    "uuid": "434f5c3e-f32d-4e16-8cdb-c7b049c058e2",
    "name": "o_antiphons",
    "title": "Advent \"O\" Antiphons",
    "description": "The traditional \"O\" Antiphons are used before and after the first canticle in Evening Prayer during the last eight days of Advent. You can use literal translations of the original Latin, or the familiar paraphrases used in the hymn \"O Come, O Come Emmanuel\"",
    "site": 1,
    "site_name": "Daily Office",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 17,
    "options": [
      {
        "uuid": "32986315-85c4-4620-9ce2-4d58039fe830",
        "name": "Literal",
        "description": "Literal translation of the original Latin",
        "value": "literal",
        "order": 0
      },
      {
        "uuid": "9f229435-afc7-448e-a535-5a4f5beef7d4",
        "name": "Hymnal",
        "description": "Paraphrase used in, <em>O Come, O Come Emmanuel</em>",
        "value": "paraphrase",
        "order": 1
      },
      {
        "uuid": "291c786f-476d-4ce3-be39-31578da8083f",
        "name": "Latin",
        "description": "Original Latin",
        "value": "latin",
        "order": 2
      },
      {
        "uuid": "8a06b75c-b409-45bb-8af8-cf8b64e1df20",
        "name": "None",
        "description": "Hide the antiphons",
        "value": "none",
        "order": 3
      }
    ]
  },
  {
    "uuid": "ec4002c6-dfde-4b77-8b65-125bc09c1ab2",
    "name": "family_readings",
    "title": "Readings",
    "description": "",
    "site": 2,
    "site_name": "Family Prayer",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 0,
    "options": [
      {
        "uuid": "e9ebd09e-e37a-4587-8344-775477a26638",
        "name": "Brief",
        "description": "A brief scripture reading appointed for the time of day",
        "value": "brief",
        "order": 0
      },
      {
        "uuid": "b74cbba0-cc17-4ce9-a68a-60110ff4114d",
        "name": "Long",
        "description": "A longer scripture reading from the continuous lectionary",
        "value": "long",
        "order": 1
      }
    ]
  },
  {
    "uuid": "2430742c-7824-47dd-9ed1-6cd59d636a23",
    "name": "family_reading_audio",
    "title": "Reading Audio",
    "description": "Show or hide an audio player to listen to the scripture readings during Morning and Evening Prayer.  Audio is provided by esv.org and currently does not include the Deuterocanon/Apocrypha.",
    "site": 2,
    "site_name": "Family Prayer",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 1,
    "options": [
      {
        "uuid": "5f01007e-6720-4060-b04c-a16ff1ac8643",
        "name": "Disable Audio",
        "description": "No audio controls for scripture readings",
        "value": "off",
        "order": 0
      },
      {
        "uuid": "37591c2b-06c9-4928-b036-f5cbf0f464dc",
        "name": "Enable Audio",
        "description": "Enable audio player for scripture readings",
        "value": "on",
        "order": 1
      }
    ]
  },
  {
    "uuid": "ccb625a1-b8a7-47e0-a0d6-ab8850681cfc",
    "name": "family_collect",
    "title": "Collect",
    "description": "",
    "site": 2,
    "site_name": "Family Prayer",
    "setting_type": 1,
    "setting_type_name": "Settings",
    "order": 2,
    "options": [
      {
        "uuid": "e0354171-18db-40e4-a42a-cd5c8e37b2ca",
        "name": "By Time of Day",
        "description": "The prayer appointed for the time of day from Family Prayer",
        "value": "time_of_day",
        "order": 0
      },
      {
        "uuid": "bd6cae4a-4db8-4e1e-aa57-06822bb2bef5",
        "name": "By Day of Week",
        "description": "The prayer appointed for the day of the week from the Daily Office",
        "value": "day_of_week",
        "order": 1
      },
      {
        "uuid": "02418ad2-1e51-493c-b0da-38186ac3a426",
        "name": "By Day of the Year",
        "description": "The prayer appointed for the specific day of the year (or the previous Sunday if there is no feast)",
        "value": "day_of_year",
        "order": 2
      }
    ]
  },
  {
    "uuid": "8d620a08-11ed-43d5-b088-b6004bca859c",
    "name": "theme",
    "title": "Visual Theme",
    "description": "Use light mode or dark mode, or default to your computer's setting for light or dark mode",
    "site": 2,
    "site_name": "Family Prayer",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 0,
    "options": [
      {
        "uuid": "af0cc7a8-e5b8-433e-a5a8-c70ffe24a44d",
        "name": "Use Computer Setting",
        "description": "The long form of the intro and absolution are used every day",
        "value": "theme-auto",
        "order": 0
      },
      {
        "uuid": "cd38567a-4786-46c1-b058-5dab4a20f956",
        "name": "Light Mode",
        "description": "The long form of the intro and absolution are used only on fast days",
        "value": "theme-light",
        "order": 1
      },
      {
        "uuid": "dcb3ab3f-31e3-47c3-a9a4-7d85664e729d",
        "name": "Dark Mode",
        "description": "The short form of the intro and absolution are used every day",
        "value": "theme-dark",
        "order": 2
      }
    ]
  },
  {
    "uuid": "1c932b4c-c381-4df8-972c-d66071986dda",
    "name": "family-opening-setence",
    "title": "Opening Sentence",
    "description": "Use the same opening sentences each day based on the time of the day, or use the seasonal options from the Daily Office",
    "site": 2,
    "site_name": "Family Prayer",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 1,
    "options": [
      {
        "uuid": "f09996a0-6163-4433-a09a-c8c4590b6d32",
        "name": "Fixed by Time of Day",
        "description": "No creed",
        "value": "family-opening-sentence-fixed",
        "order": 0
      },
      {
        "uuid": "108264b7-aa87-4a1e-99be-cc192919b96f",
        "name": "Seasonal",
        "description": "Include Creed",
        "value": "family-opening-sentence-seasonaal",
        "order": 1
      }
    ]
  },
  {
    "uuid": "22999278-ec94-4baf-adb3-503ad22793bf",
    "name": "family-creed",
    "title": "Apostles' Creed",
    "description": "Include the Apostle's Creed before the prayers during 'In the Morning' and 'In the Early Evening' Family Prayer",
    "site": 2,
    "site_name": "Family Prayer",
    "setting_type": 2,
    "setting_type_name": "Additional Settings",
    "order": 2,
    "options": [
      {
        "uuid": "3cd34488-92a7-44a3-8fa9-c85a5636ec0c",
        "name": "No",
        "description": "No creed",
        "value": "family-creed-no",
        "order": 0
      },
      {
        "uuid": "e7fb1472-cce6-4f24-921a-51c4a54d7563",
        "name": "Yes",
        "description": "Include Creed",
        "value": "family-creed-yes",
        "order": 1
      }
    ]
  }
]

export default {
  data() {
    return {
      counter: 0,
      settings: settings,
    }
  },
  name: "Settings",
  components: {
    RadioGroup,
    RadioGroupDescription,
    RadioGroupLabel,
    RadioGroupOption,
  },
  mounted() {
    setInterval(() => {
      this.counter++
    }, 1000)
  },
  setup() {
    const selected = ref(settings[0])

    return {
      selected,
    }
  },
};
</script>
