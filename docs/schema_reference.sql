-- Схема PostgreSQL: каталог продукции Faserkraft

CREATE TABLE product_categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    sort_order INT DEFAULT 0,
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    legacy_wp_id INT UNIQUE,
    category_id INT REFERENCES product_categories(id),
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    short_description TEXT,
    description TEXT,
    membrane_material VARCHAR(255),
    status VARCHAR(50) DEFAULT 'published',
    seo_title VARCHAR(500),
    seo_description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE product_specifications (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    group_name VARCHAR(255) NOT NULL,
    parameter_name VARCHAR(500) NOT NULL,
    parameter_value VARCHAR(500),
    sort_order INT DEFAULT 0
);

CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url VARCHAR(1000) NOT NULL,
    sort_order INT DEFAULT 0
);

CREATE TABLE product_documents (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    title VARCHAR(500),
    file_url VARCHAR(1000) NOT NULL,
    sort_order INT DEFAULT 0
);

CREATE TABLE redirects (
    id SERIAL PRIMARY KEY,
    source_path VARCHAR(500) UNIQUE NOT NULL,
    target_path VARCHAR(500) NOT NULL,
    http_status INT DEFAULT 301,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT INTO product_categories (slug, name) VALUES
('ultrafiltracionnye-membrannye-moduli', 'Ультрафильтрационные мембранные модули'),
('pogruzhnoj-membrannyj-filtr', 'Погружные мембранные фильтры');
