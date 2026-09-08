export type CounterOfflineOrder = { localId: string; idempotencyKey: string; payload: Record<string, unknown>; createdAt: string; status: "pending" | "failed"; retryCount: number; lastError?: string };

const DB_NAME = "menutap-counter";
const STORE = "orders";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: "localId" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueCounterOrder(order: CounterOfflineOrder): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => { const tx = db.transaction(STORE, "readwrite"); tx.objectStore(STORE).put(order); tx.oncomplete = () => resolve(); tx.onerror = () => reject(tx.error); });
  db.close();
}

export async function listQueuedCounterOrders(): Promise<CounterOfflineOrder[]> {
  const db = await openDb();
  const rows = await new Promise<CounterOfflineOrder[]>((resolve, reject) => { const request = db.transaction(STORE).objectStore(STORE).getAll(); request.onsuccess = () => resolve(request.result as CounterOfflineOrder[]); request.onerror = () => reject(request.error); });
  db.close();
  return rows;
}

export async function removeQueuedCounterOrder(localId: string): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => { const tx = db.transaction(STORE, "readwrite"); tx.objectStore(STORE).delete(localId); tx.oncomplete = () => resolve(); tx.onerror = () => reject(tx.error); });
  db.close();
}

export async function updateQueuedCounterOrder(order: CounterOfflineOrder): Promise<void> { const db = await openDb(); await new Promise<void>((resolve, reject) => { const tx = db.transaction(STORE, "readwrite"); tx.objectStore(STORE).put(order); tx.oncomplete = () => resolve(); tx.onerror = () => reject(tx.error); }); db.close(); }
