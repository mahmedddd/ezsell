/**
 * Shared NLP utilities for search — mirrors the backend logic in listings.py.
 * Any change here should be reflected in the backend stemmer/tokenizer too.
 */

const STOPWORDS = new Set([
    'a', 'an', 'the', 'and', 'or', 'for', 'with', 'in', 'on', 'at',
    'to', 'of', 'is', 'it', 'its', 'be', 'as', 'by', 'are', 'was',
    'my', 'i', 'me', 'we', 'you', 'he', 'she', 'they', 'this', 'that',
]);

/**
 * Basic English suffix stemmer — strips plurals and -ing forms.
 * Mirrors _stem() in backend/routers/listings.py.
 */
export function stem(word: string): string {
    const w = word.toLowerCase();
    if (w.endsWith('ing') && w.length > 5) return w.slice(0, -3);   // selling→sell
    if (w.endsWith('ies') && w.length > 4) return w.slice(0, -3) + 'y'; // stories→story
    if (w.endsWith('ers') && w.length > 4) return w.slice(0, -1);    // sellers→seller
    if (w.endsWith('es') && w.length > 4) return w.slice(0, -2);   // couches→couch
    if (w.endsWith('s') && w.length > 3) return w.slice(0, -1);   // beds→bed
    return w;
}

/**
 * Tokenize a search query into meaningful words (lowercased, stopwords removed).
 * Mirrors the tokenizer in backend get_listings().
 */
export function tokenize(query: string): string[] {
    const raw = query.trim().split(/[\s\-_/,]+/);
    const words = raw
        .map(w => w.toLowerCase())
        .filter(w => w.length >= 2 && !STOPWORDS.has(w));
    return words.length > 0 ? words : [query.trim().toLowerCase()];
}

/**
 * Returns true if a listing matches the search query.
 * Checks title, description, brand — same fields as the backend.
 * Every token in the query must appear (as original or stemmed) in at least one field.
 */
export function listingMatchesSearch(listing: any, query: string): boolean {
    if (!query.trim()) return true;

    const words = tokenize(query);
    // Search across ALL listing fields — mirrors expanded backend search
    const fields = [
        listing.title || '',
        listing.description || '',
        listing.brand || '',
        listing.category || '',
        listing.condition || '',
        listing.furniture_type || '',
        listing.material || '',
        listing.location || '',
    ].map(f => f.toLowerCase());

    return words.every(word => {
        const stemmedWord = stem(word);
        return fields.some(field => {
            // Build a stemmed version of the field for comparison
            const stemmedField = field.split(/\s+/).map(stem).join(' ');
            return (
                field.includes(word) ||
                field.includes(stemmedWord) ||
                stemmedField.includes(stemmedWord)
            );
        });
    });
}
