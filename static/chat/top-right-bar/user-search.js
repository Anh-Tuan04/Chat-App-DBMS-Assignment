export async function searchUsers(query) {
    let response;
    try {
        response = await fetch(
            `/api/users/search?username=${encodeURIComponent(query)}`,
            { credentials: 'same-origin' }
        );
    } catch (error) {
        throw new Error('Could not search users');
    }

    let body;
    try {
        body = await response.json();
    } catch (error) {
        throw new Error('Invalid user search response');
    }

    if (!response.ok) {
        throw new Error(body?.message || 'Could not search users');
    }
    if (!Array.isArray(body)) {
        throw new Error('Invalid user search response');
    }
    return body;
}
