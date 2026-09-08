import { expect, test } from "@playwright/test";
import { connectionLabel, kitchenLabel, kitchenStage } from "../src/features/staff/status";

test("staff status mapping keeps held out of the permanent kitchen lanes", () => {
  expect(kitchenStage({ status: "pending", kitchen: { stage: "pending", is_held: true } })).toBe("pending");
  expect(kitchenLabel("preparing")).toBe("Preparing");
  expect(connectionLabel(true, 0, true)).toBe("Status unavailable");
});
