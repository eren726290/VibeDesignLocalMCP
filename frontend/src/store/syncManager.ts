// SyncManager — pausable polling controller
// pauseSync() / resumeSync() wrap any local change → backend PUT cycle.
// While paused (count > 0), the polling loop skips setDocument.

let _pauseCount = 0;

export const syncManager = {
  pauseRef: { get count() { return _pauseCount; } },

  pauseSync() {
    _pauseCount++;
  },

  resumeSync() {
    if (_pauseCount > 0) _pauseCount--;
  },
};
