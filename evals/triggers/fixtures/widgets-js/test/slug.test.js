import { test } from "node:test";
import assert from "node:assert/strict";
import { slug } from "../index.js";

test("slug joins words with dashes", () => {
  assert.equal(slug(" Blue Widget "), "blue-widget");
});
