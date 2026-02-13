// validate_meta.mjs (profile-aware)
import fs from "fs";
import Ajv from "ajv";
import addFormats from "ajv-formats";

const SCHEMA_PATH = "FUNCTIONcalled_Metadata_Sidecar.v1.1.schema.json";
const schema = JSON.parse(fs.readFileSync(SCHEMA_PATH, "utf8"));

const ajv = new Ajv({allErrors:true, strict:false});
addFormats(ajv);
const validate = ajv.compile(schema);

let ok = true;
for (const p of process.argv.slice(2)) {
  const data = JSON.parse(fs.readFileSync(p, "utf8"));
  const valid = validate(data);
  if (valid) {
    console.log(`✅ ${p}`);
  } else {
    ok = false;
    console.log(`❌ ${p}`);
    for (const err of validate.errors) {
      const where = err.instancePath || "(root)";
      console.log("  -", where, err.message);
    }
  }
}
process.exit(ok ? 0 : 1);
