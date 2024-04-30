const schemaCache = {};

const fetchSchema = async (conn) => {

    if (schemaCache[conn]) {
        return schemaCache[conn];
    }

    try {
        const response = await fetch(`../schema.json/${conn}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const schema = await response.json();
        schemaCache[conn] = schema;  // Cache the schema
        return schema;
    } catch (error) {
        console.error('Error fetching table schema:', error);
        throw error;  // Re-throw to handle it in the calling function
    }
};

export const SchemaSvc = {
    get: fetchSchema
};
