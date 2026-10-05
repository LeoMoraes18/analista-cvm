CREATE EXTENSION IF NOT EXISTS unaccent;

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

CREATE TABLE IF NOT EXISTS conta (
    cd_cvm       INTEGER NOT NULL,
    demonstracao TEXT    NOT NULL,
    consolidado  BOOLEAN NOT NULL,
    dt_refer     DATE    NOT NULL,
    versao       INTEGER NOT NULL,
    dt_ini_exerc DATE,
    dt_fim_exerc DATE    NOT NULL,
    cd_conta     TEXT    NOT NULL,
    ds_conta     TEXT    NOT NULL,
    vl_conta     NUMERIC(20, 2),
    PRIMARY KEY (cd_cvm, demonstracao, consolidado, dt_fim_exerc, cd_conta)
);

CREATE TABLE IF NOT EXISTS inconsistencia (
    cd_cvm INTEGER NOT NULL,
    demonstracao TEXT NOT NULL,
    consolidado BOOLEAN NOT NULL,
    dt_fim_exerc DATE NOT NULL,
    motivo TEXT NOT NULL,
    PRIMARY KEY (cd_cvm, demonstracao, consolidado, dt_fim_exerc)
);