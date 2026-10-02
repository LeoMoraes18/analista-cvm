CREATE TABLE IF NOT EXISTS carga (
    arquivo TEXT PRIMARY KEY,
    linhas  INTEGER NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS empresa (
    cd_cvm          INTEGER PRIMARY KEY,
    cnpj            TEXT NOT NULL,
    denom_social    TEXT NOT NULL,
    denom_comerc    TEXT,
    setor_ativ      TEXT,
    situacao        TEXT,
    dt_registro     DATE,
    dt_cancelamento DATE,
    uf              TEXT
);