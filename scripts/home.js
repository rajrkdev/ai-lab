(function () {
  var cmd = "explore --interactive --depth=expert";
  var el = document.getElementById("typed-cmd");
  var cursor = document.getElementById("cursor");
  var output = document.getElementById("terminal-output");
  if (!el) return;

  var i = 0;
  var timer = setInterval(function () {
    el.textContent += cmd[i++];
    if (i >= cmd.length) {
      clearInterval(timer);
      if (cursor) cursor.style.display = "none";
      setTimeout(function () {
        if (output) output.style.display = "block";
      }, 300);
    }
  }, 55);
})();
