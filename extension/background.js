/* Runs in the service-worker context */
chrome.runtime.onInstalled.addListener(() => {
  // Make a click on the toolbar icon open the side panel
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});
