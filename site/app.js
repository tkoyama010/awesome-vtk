// Client side search and category filtering for the Awesome VTK gallery.
(function () {
  "use strict";

  var search = document.getElementById("search");
  var chips = Array.prototype.slice.call(
    document.querySelectorAll("#chips .chip"),
  );
  var sections = Array.prototype.slice.call(
    document.querySelectorAll(".section"),
  );
  var empty = document.getElementById("empty");
  var activeCategory = "all";

  function apply() {
    var query = search.value.trim().toLowerCase();
    var visible = 0;

    sections.forEach(function (section) {
      var matchesCategory =
        activeCategory === "all" ||
        section.getAttribute("data-category") === activeCategory;
      var shown = 0;

      Array.prototype.forEach.call(
        section.querySelectorAll(".card"),
        function (card) {
          var matches =
            matchesCategory &&
            (query === "" ||
              card.getAttribute("data-search").indexOf(query) !== -1);
          card.hidden = !matches;
          if (matches) {
            shown += 1;
          }
        },
      );

      section.hidden = shown === 0;
      visible += shown;
    });

    empty.hidden = visible !== 0;
  }

  search.addEventListener("input", apply);

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      activeCategory = chip.getAttribute("data-filter");
      chips.forEach(function (other) {
        other.classList.toggle("chip--active", other === chip);
      });
      apply();
    });
  });

  // Preview images come from GitHub's Open Graph service, which rate limits
  // bursts of requests. Retry once with a jittered delay, then drop the image
  // so the coloured monogram underneath stays visible.
  Array.prototype.forEach.call(
    document.querySelectorAll(".card__image"),
    function (image) {
      var retried = false;
      image.addEventListener("error", function () {
        if (retried) {
          image.remove();
          return;
        }
        retried = true;
        var source = image.src;
        window.setTimeout(
          function () {
            image.src = source + "?retry=1";
          },
          800 + Math.random() * 1600,
        );
      });
    },
  );

  apply();
})();
