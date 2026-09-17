(() => {
  const dialog = document.querySelector("#rating-dialog");
  const openButtons = document.querySelectorAll("[data-open-rating]");
  openButtons.forEach((button) => {
    button.addEventListener("click", () => dialog?.showModal());
  });

  const search = document.querySelector("#book-search");
  const results = document.querySelector("#book-results");
  const selectedId = document.querySelector("#selected-book-id");
  const selectedBook = document.querySelector("#selected-book");
  const ratingForm = document.querySelector("#rating-form");
  const ratingError = document.querySelector("#rating-error");
  let searchTimer;
  let controller;

  const hideResults = () => {
    if (!results || !search) return;
    results.hidden = true;
    search.setAttribute("aria-expanded", "false");
  };

  const chooseBook = (book) => {
    if (!selectedId || !selectedBook || !search) return;
    selectedId.value = String(book.id);
    search.value = book.title;
    selectedBook.innerHTML = "";
    const title = document.createElement("strong");
    const metadata = document.createElement("small");
    title.textContent = book.title;
    metadata.textContent = [book.authors, book.category].filter(Boolean).join(" · ");
    selectedBook.append(title, metadata);
    selectedBook.hidden = false;
    hideResults();
  };

  const showSearchResults = (books) => {
    if (!results || !search) return;
    results.innerHTML = "";
    if (!books.length) {
      const empty = document.createElement("button");
      empty.type = "button";
      empty.disabled = true;
      empty.textContent = "No matching books found";
      results.append(empty);
    }
    books.forEach((book) => {
      const option = document.createElement("button");
      option.type = "button";
      option.role = "option";
      const title = document.createElement("strong");
      const metadata = document.createElement("small");
      title.textContent = book.title;
      metadata.textContent = [book.authors, book.category].filter(Boolean).join(" · ");
      option.append(title, metadata);
      option.addEventListener("click", () => chooseBook(book));
      results.append(option);
    });
    results.hidden = false;
    search.setAttribute("aria-expanded", "true");
  };

  search?.addEventListener("input", () => {
    if (selectedId) selectedId.value = "";
    if (selectedBook) selectedBook.hidden = true;
    clearTimeout(searchTimer);
    const query = search.value.trim();
    if (query.length < 2) {
      hideResults();
      return;
    }
    searchTimer = setTimeout(async () => {
      controller?.abort();
      controller = new AbortController();
      try {
        const response = await fetch(`/api/books/search?q=${encodeURIComponent(query)}`, {
          signal: controller.signal,
          headers: { Accept: "application/json" },
        });
        if (!response.ok) throw new Error("Search failed");
        showSearchResults(await response.json());
      } catch (error) {
        if (error.name !== "AbortError") showSearchResults([]);
      }
    }, 220);
  });

  ratingForm?.addEventListener("submit", (event) => {
    const rating = ratingForm.querySelector("input[name='rating']:checked");
    if (!selectedId?.value || !rating) {
      event.preventDefault();
      if (ratingError) {
        ratingError.textContent = !selectedId?.value
          ? "Choose a book from the search results."
          : "Choose a rating from 1 to 5 stars.";
        ratingError.hidden = false;
      }
    }
  });

  const toast = document.querySelector(".toast");
  if (toast) window.setTimeout(() => toast.remove(), 5000);

  // WebMCP exposes the same rating action as the visible form where supported.
  const modelContext = document.modelContext;
  if (modelContext?.registerTool && ratingForm) {
    const token = document.querySelector("meta[name='csrf-token']")?.content;
    void Promise.resolve(
      modelContext.registerTool({
        name: "save_reading_rating",
        title: "Save reading rating",
        description: "Add or update one catalog book in this reader's history with a 1–5 rating.",
        inputSchema: {
          type: "object",
          properties: {
            bookId: { type: "integer", minimum: 1 },
            rating: { type: "integer", minimum: 1, maximum: 5 },
          },
          required: ["bookId", "rating"],
          additionalProperties: false,
        },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        async execute(input) {
          if (!Number.isInteger(input?.bookId) || !Number.isInteger(input?.rating) || input.rating < 1 || input.rating > 5) {
            throw new TypeError("bookId and a rating from 1 to 5 are required");
          }
          const response = await fetch("/api/ratings", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRF-Token": token || "" },
            body: JSON.stringify({ book_id: input.bookId, rating: input.rating }),
          });
          if (!response.ok) throw new Error(`Rating was not saved (${response.status})`);
          const result = await response.json();
          const total = document.querySelector("[data-total-read]");
          if (total) total.textContent = String(result.total_read);
          return { bookId: result.book_id, rating: result.rating, totalRead: result.total_read };
        },
      }),
    ).catch(() => {});
  }
})();
