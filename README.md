# Recortar Vídeo

Escolha um formato, arraste o mouse sobre o vídeo e salve uma **cópia recortada**. O original continua na mesma pasta, sem ser alterado, movido ou apagado.

**Recorte livre · 1:1 · 4:5 · 9:16 · 16:9 · 4:3 · Proporção original**

O programa recorta a imagem durante toda a duração do vídeo. A linha do tempo serve para conferir o enquadramento em outros momentos.

## O que instalar uma única vez

Este guia é para **Windows 10/11 de 64 bits**.

| Item | Como será instalado |
| --- | --- |
| Python 3.12 | Pela Microsoft Store |
| OpenCV e Pillow | Com um comando explicado abaixo |
| FFmpeg, com H.264/libx264 | Com um comando explicado abaixo |

As bibliotecas auxiliares, como NumPy, são instaladas junto com o OpenCV. A janela usa o Tkinter, incluído no Python oficial. Não precisa instalar Git para baixar ou usar o projeto.

## 1. Instalar o Python pela loja

1. Clique no menu **Iniciar** do Windows.
2. Digite **Microsoft Store** e abra a loja.
3. Na busca da loja, digite **Python 3.12**.
4. Escolha o aplicativo **Python 3.12**, publicado por **Python Software Foundation**.
5. Clique em **Obter** ou **Instalar** e aguarde a conclusão. Não precisa abrir o aplicativo do Python depois de instalar.
6. Feche os terminais que estavam abertos. Abra o menu Iniciar, pesquise **Terminal** ou **PowerShell** e abra.
7. Copie este comando, cole no terminal e pressione **Enter**:

```powershell
python --version
```

Se aparecer `Python 3.12...`, deu certo. Se outro Python já estiver instalado, confirme que ele tem as bibliotecas e o Tkinter antes de continuar. A versão usada na verificação do programa foi a 3.12.

## 2. Instalar o FFmpeg

No mesmo terminal, cole este comando e pressione **Enter**:

```powershell
winget install --id Gyan.FFmpeg --exact --source winget
```

1. Aguarde o download e a instalação. Se forem exibidos termos ou uma confirmação do Windows, leia e confirme para continuar.
2. **Feche o terminal e abra outro** para o Windows reconhecer a instalação.
3. Confira com:

```powershell
ffmpeg -version
```

Se aparecer o nome FFmpeg e informações de versão, está pronto. Esse caminho evita ter que configurar pastas manualmente no PATH.

**Se aparecer “winget não é reconhecido”:** abra a Microsoft Store, pesquise **Instalador de Aplicativo** (**App Installer**), da **Microsoft**, e instale ou atualize. Feche o terminal, abra novamente e repita o comando do FFmpeg. Se o computador da empresa bloquear instalações, será necessário pedir a instalação ao responsável.

Alternativa: a [página oficial do FFmpeg](https://ffmpeg.org/download.html) indica os pacotes para Windows. Nesse caso, extraia o pacote e adicione a pasta que contém `ffmpeg.exe` ao PATH.

## 3. Baixar o programa

1. Abra [AntonioLucas-rs/recortar-video](https://github.com/AntonioLucas-rs/recortar-video).
2. Clique no botão **Code** e depois em **Download ZIP**.
3. Abra a pasta **Downloads** do Windows.
4. Clique com o botão direito no ZIP baixado e escolha **Extrair Tudo… → Extrair**.
5. Entre na pasta extraída, onde estão `recortar_video.py`, `requirements.txt` e este manual. Se aparecer outra pasta dentro, abra-a até encontrar os arquivos.

## 4. Instalar as bibliotecas

1. Dentro dessa pasta, clique na **barra de endereço** do Explorador de Arquivos, onde aparece o caminho da pasta.
2. Digite `powershell` e pressione **Enter**. Isso abre o terminal já na pasta correta.
3. Cole o comando abaixo e pressione **Enter**:

```powershell
python -m pip install -r requirements.txt
```

Espere a instalação terminar. Essa etapa precisa ser repetida apenas ao usar outro ambiente Python ou quando atualizar as dependências do programa. Não precisa executar como administrador em uma instalação normal do Python pela Store.

## 5. Colocar junto dos vídeos e abrir

1. Copie **somente `recortar_video.py`** para a pasta em que estão os vídeos que você quer recortar.
2. Nessa pasta dos vídeos, clique na barra de endereço, digite `powershell` e pressione **Enter**.
3. Cole e execute:

```powershell
python recortar_video.py
```

A janela do programa vai abrir. Depois da instalação, você só precisa repetir esse último comando para usar novamente.

O script procura os vídeos diretamente na própria pasta, mesmo se for iniciado de outro lugar. Ele não procura em subpastas. Depois de instalar as dependências, o manual e o `requirements.txt` podem ficar na pasta do download; apenas o script precisa acompanhar os vídeos.

Exemplo:

```text
Meus vídeos/
├── recortar_video.py
├── viagem.mp4
├── festa.mov
└── videos_prontos/     ← criada automaticamente para as cópias
```

## Como recortar

1. Na parte inferior da janela, escolha **Recorte livre** ou um formato pronto. **Original** mantém a proporção da imagem de entrada.
2. Clique e arraste sobre o vídeo para desenhar a área que vai ficar. Nos formatos prontos, a proporção fica travada.
3. Para reposicionar, arraste **dentro da seleção**.
4. Para desenhar novamente, pressione **Esc** ou comece outro arrasto fora da seleção. Trocar o formato também limpa a seleção. O formato escolhido continua ativo no próximo vídeo.
5. Se quiser, altere o campo **Título** para definir o nome da cópia e o título gravado no arquivo.
6. Clique em **Salvar** ou pressione **Enter**. A cópia vai para **`videos_prontos`**, e o próximo vídeo é aberto.
7. Para deixar um vídeo para depois, clique em **Pular**. Ele continua na pasta e aparecerá de novo na próxima execução.

**Salvar e Pular preservam os originais.** O programa não tem botão de excluir e não cria uma pasta de vídeos deletados. Se já existir uma cópia com o mesmo nome, o novo resultado recebe um número, como `viagem (2).mp4`.

Sem seleção, Salvar cria uma cópia com o tamanho completo, sem recomprimir a imagem e o áudio. Escolher um formato sem desenhar uma seleção não faz um recorte automático.

### Conferir outros momentos do vídeo

- Clique ou arraste na linha do tempo, ou clique nas miniaturas.
- **← / →**: volta ou avança aproximadamente um segundo.
- **, / .**: volta ou avança um quadro.
- Dentro do campo Título, as teclas servem para editar o texto.

A prévia não reproduz áudio. O programa mantém a duração completa do vídeo; não é um editor para cortar o começo ou o fim.

### Qualidade e organização

- Com recorte, a saída é **MP4/H.264**, com qualidade alta (`CRF 18`). Recortar exige recodificar a imagem: pode haver alguma perda de qualidade e o tamanho do arquivo pode mudar.
- O áudio original é copiado quando compatível com MP4. Quando necessário, é convertido para AAC.
- Os formatos prontos mantêm a proporção exata. Para compatibilidade, largura e altura são pares; esse ajuste pode reduzir alguns pixels. A janela mostra as dimensões finais.
- O programa solicita a remoção dos metadados copiados e capítulos, mantendo o novo título. Informações visíveis dentro da imagem continuam presentes.
- Cada subpasta de `videos_prontos` aparece como um botão: clicar salva o vídeo nela. **+ Nova pasta** pede o nome, cria a subpasta e já salva o vídeo atual.
- A exportação acontece em segundo plano, um vídeo por vez. Ao fechar a janela, **aguarde o terminal terminar** antes de fechá-lo. O resumo informa os arquivos salvos e os erros.
- Vídeos concluídos são registrados em `videos_prontos/.feitos.txt` e não aparecem novamente. Para refazer um, remova a linha com seu nome desse registro. Para refazer todos, remova o registro. As cópias existentes são preservadas.
- Uma exportação que falhar não marca o original como concluído. Após uma interrupção forçada, pode restar um arquivo `.parcial` na pasta de saída.

Entradas reconhecidas: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.m4v` e `.wmv`. A leitura também depende do codec do vídeo.

## Se algo não funcionar

| Situação | Como resolver |
| --- | --- |
| `python` abre a loja ou não é reconhecido | Confirme que o Python terminou de instalar. Feche e reabra o terminal. Pesquise **Gerenciar aliases de execução de aplicativo** no Windows e confira os atalhos do Python instalado. |
| FFmpeg não encontrado | Confira `ffmpeg -version` em um terminal novo. Se necessário, repita a instalação do passo 2. |
| `requirements.txt` não encontrado | Execute a instalação dentro da pasta extraída do download, onde está esse arquivo. |
| Faltam bibliotecas, `cv2` ou `PIL` | Execute `python -m pip install opencv-python Pillow` com o mesmo Python que abre o programa. |
| Erro de Tkinter | Execute `python -m tkinter`. Deve abrir uma janela de demonstração. Se não abrir, reinstale o Python oficial com suporte a Tcl/Tk. |
| Nenhum vídeo para recortar | Coloque o script junto dos vídeos. Confira as extensões e se eles já estão registrados em `.feitos.txt`. |
| Seleção muito pequena | Arraste uma área maior para o formato escolhido. |
| Não consegui abrir / erro ao salvar | Confira se o vídeo abre em um player e leia o erro no terminal. O arquivo pode estar corrompido ou usar um codec indisponível. |

## Arquivos do projeto

Para distribuir este programa, são necessários somente:

- `recortar_video.py` — programa independente.
- `requirements.txt` — bibliotecas para a instalação.
- `README.md` — este guia.
- `.gitignore` — evita incluir mídias, resultados e arquivos temporários nos commits.

O upload manual pelo site do GitHub não aplica o `.gitignore`; selecione apenas os arquivos do projeto. Os scripts de fotos não são necessários para este programa.

## Referências

- [Python oficial pela Microsoft Store](https://docs.python.org/3.12/using/windows.html#the-microsoft-store-package)
- [Comando de instalação do WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/install)
- [Pacote Gyan.FFmpeg no catálogo do WinGet](https://github.com/microsoft/winget-pkgs/tree/master/manifests/g/Gyan/FFmpeg)
- [OpenCV](https://pypi.org/project/opencv-python/) e [Pillow](https://pypi.org/project/Pillow/)
