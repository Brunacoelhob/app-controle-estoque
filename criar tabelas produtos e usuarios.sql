SET FOREIGN_KEY_CHECKS = 0;

-- Tabela de Usuários
CREATE TABLE TBL_USUARIO (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    Nome_usuario VARCHAR(100) NOT NULL,
    Email_usuario VARCHAR(100) NOT NULL UNIQUE,
    Senha_usuario VARCHAR(255) NOT NULL,
    Perfil_usuario VARCHAR(45) NOT NULL, -- Ex: 'admin' ou 'comum'
    foto_url VARCHAR(255) DEFAULT 'default.png'
);

-- Tabela de Produtos
CREATE TABLE TBL_PRODUTO (
    id_produto INT AUTO_INCREMENT PRIMARY KEY,
    Nome_produto VARCHAR(100) NOT NULL,
    Quantidade_produto INT DEFAULT 0,
    Minimo_produto INT DEFAULT 1
);

-- Tabela de Movimentações
CREATE TABLE TBL_MOVIMENTACAO (
    id_movimentacao INT AUTO_INCREMENT PRIMARY KEY,
    Tipo_movimentacao VARCHAR(100) NOT NULL,
    Quantidade INT NOT NULL,
    Data DATE NOT NULL,
    TBL_USUARIO_id INT,
    TBL_PRODUTO_id_produto INT,
    FOREIGN KEY (TBL_USUARIO_id) REFERENCES TBL_USUARIO(id_usuario),
    FOREIGN KEY (TBL_PRODUTO_id_produto) REFERENCES TBL_PRODUTO(id_produto)
);

-- Reativa as restrições
SET FOREIGN_KEY_CHECKS = 1;