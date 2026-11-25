# Ableton Express · página de vendas

A página inteira funciona como um set do Ableton Live.

| Arquivo | O que é |
|---|---|
| `index.html` | Fonte da página (os prints dos alunos vêm de `assets/depoimentos/`) |
| `dist/ableton-express.html` | **Arquivo final, tudo num arquivo só** (imagens embutidas), pra subir no WordPress |
| `build.py` | Gera o `dist/` a partir do `index.html`: `python3 build.py` |
| `legacy/` | Versão anterior da página, guardada de referência |

## O que tem na página
- **Barra de transporte** fixa no topo: play/stop, BPM (arraste ou use como tap tempo), metrônomo, posição que anda com a rolagem, teclado MIDI do computador (tecla `M`) e CPU.
- **Session View tocável** no topo: 6 faixas × 4 cenas em Sol maior, tudo sintetizado com Web Audio (sem arquivo de áudio). Os clipes entram quantizados no próximo compasso. `Espaço` dá play e stop.
- **Crossfader A/B** (sem dominar / dominando), **Record Arm** no “pra quem é”, **Arrangement** dos módulos com playhead que segue a rolagem, **automação** da trajetória, **Instrument Rack** com macros, **Drum Rack** tocável no “o que vem junto”, **Loop** de 7 dias na garantia e **Browser** no FAQ.
- **Info View** (desktop): passe o mouse em qualquer elemento e aparece a explicação no canto, como no Live.
- Respeita `prefers-reduced-motion`. O áudio só toca depois de um clique.
