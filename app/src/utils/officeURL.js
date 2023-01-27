import { DynamicStorage } from "@/helpers/storage";
import store from "@/store";

async function extraCollects(office_str, serviceType = "office") {
  if (serviceType != "office") {
    return "";
  }
  const full_office_name = office_str
    .replace("_", " ")
    .toLowerCase()
    .split(" ")
    .map((s) => s.charAt(0).toUpperCase() + s.substring(1))
    .join(" ");
  const extraCollects =
    JSON.parse(await DynamicStorage.getItem("extraCollects")) || "";
  if (!extraCollects) {
    return "";
  }
  const office_extra_collects = Object.prototype.hasOwnProperty.call(
    extraCollects,
    full_office_name
  )
    ? extraCollects[full_office_name].join(",")
    : [];
  return office_extra_collects;
}

export async function getOfficeURL(office_str, office_type_str, date_str) {
  const serviceType = office_type_str;
  const settings = await store.state.settings;
  const queryString = Object.keys(settings)
    .map((key) => key + "=" + settings[key])
    .join("&");
  return (
    `${process.env.VUE_APP_API_URL}api/v1/${serviceType}/${office_str}/` +
    date_str +
    "?" +
    queryString +
    "&extra_collects=" +
    (await extraCollects(office_str, serviceType))
  );
}
