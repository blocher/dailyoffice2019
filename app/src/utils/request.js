import axios from "axios";
import { CapacitorSQLite, SQLiteConnection } from "@capacitor-community/sqlite";
import { createTablesNoEncryption } from "@/utils/utils-db-no-encryption";
import { Capacitor } from "@capacitor/core";
import { Network } from "@capacitor/network";

let global_db = null;
let global_conn = null;

class URLNotAvailableException extends Error {
  constructor(message) {
    super(message);
    this.name = "URLNotAvailableException";
  }
}

async function getDB() {
  // if (global_db) {
  //   return global_db;
  // }
  const sqlite = global_conn
    ? global_conn
    : new SQLiteConnection(CapacitorSQLite);
  global_conn = sqlite;
  const platform = Capacitor.getPlatform();
  if (platform === "web") {
    const jeepSqlite = document.createElement("jeep-sqlite");
    document.body.appendChild(jeepSqlite);
    await customElements.whenDefined("jeep-sqlite");
    await global_conn.initWebStore();
  }
  const db = await sqlite.createConnection(
    "offlineDB",
    false,
    "no-encryption",
    1,
    false
  );
  await db.open();
  await db.execute(createTablesNoEncryption);
  global_db = db;
  return db;
}

async function cacheURL(url, json) {
  try {
    json = JSON.stringify(json);
    const db = await getDB();
    let sqlcmd = "INSERT OR IGNORE INTO cache (url, json) VALUES (?, ?);";
    let res1 = await db.run(sqlcmd, [url, json]);
    sqlcmd = "UPDATE cache SET json=? WHERE url = ?;";
    const ret = await db.run(sqlcmd, [url, json]);
    await global_conn.saveToStore("offlineDB");
    console.log("Cached", url);
    return ret;
  } catch (e) {
    console.log("Error during caching", url, e);
  }
}

async function getURLOnline(url) {
  try {
    const res = await axios(url);
    if (res.status === 200) {
      await cacheURL(url, res.data);
      return res.data;
    }
    return getURLOffline(url);
  } catch (e) {
    console.log(`Error retrieving ${url} in online mode`, e);
    return getURLOffline(url);
  }
}

async function getURLOffline(url) {
  const db = await getDB();
  const sqlcmdtest = "Select url, json from cache;";
  const restest = await db.query(sqlcmdtest);
  const sqlcmd = "Select url, json from cache where url = ?;";
  const res = await db.query(sqlcmd, [url]);
  if (res.values.length > 0) {
    const data = JSON.parse(res.values[0].json);
    return data;
  }
  return false;
}

export async function getURL(url) {
  const status = await Network.getStatus();
  if (status.connected) {
    const res = await getURLOnline(url);
    if (!res) {
      throw new URLNotAvailableException(
        `URL not available online or offline: ${url}`
      );
    }
    return res;
  }
  const res = await getURLOffline(url);
  if (!res) {
    throw new URLNotAvailableException(
      `URL not available online or offline: ${url}`
    );
  }
  return res;
}

export async function precacheURL(url) {
  const status = await Network.getStatus();
  if (status.connected) {
    const offline = await getURLOffline(url);
    if (!offline) {
      await getURLOnline(url);
    }
  }
}
