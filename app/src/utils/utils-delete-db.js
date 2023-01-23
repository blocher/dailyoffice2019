export async function deleteDatabase(db) {
  let ret = await db.isExists();
  const dbName = db.getConnectionDBName();
  if (ret) {
    console.log("$$$ database " + dbName + " before delete");
    try {
      ret = await db.delete();
    } catch (err) {
      alert("Error: " + err);
    }
    console.log("$$$ database " + dbName + " after delete " + ret);
  }
  return ret;
}
