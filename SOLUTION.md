# Solution

## Lancer

```
python main.py -i instances/<instance>.txt [-p] [-m]
```

- `-p` : affiche le graphe et les chemins.
- `-m` : résout aussi le MILP exact (limite 60 s) pour comparer.

Aucune dépendance en plus de matplotlib pour la solution.
Le MILP (`milp_solution.py`, option `-m` uniquement) utilise PuLP.

## 1. Analyse du problème

C'est le problème du postier chinois.
D'après le théorème d'Euler : pour trouver un chemin eulérien (qui passe par toutes les arêtes exactement une fois), il faut avoir 0 ou 2 sommets impairs seulement.

Il est donc intuitif de supposer que, si on est obligé de repasser par une arête, la solution optimale doit repasser au plus une seule fois par cette même arête. (Si une arête est dupliquée 2 fois, on retire ces 2 copies : la parité ne change pas et le coût baisse)

Donc, si on duplique les arêtes de passage, seuls le départ et l'arrivée peuvent avoir un
degré impair.

Le coût total vaut la somme de toutes les arêtes, qui est fixe, plus le coût des arêtes dupliquées. Le problème se réduit donc à choisir les duplications les moins chères qui laissent au plus 2 sommets impairs par composante.


Observations sur les instances :

| Instance | Sommets | Arêtes | Composantes | Sommets impairs |
|---|---|---|---|---|
| hard_to_choose | 35 | 595 | 1 | 0 |
| islands | 60 | 760 | 3 | 20 / 0 / 20 |
| paris_map | 11 348 | 17 958 | 1 | 7 318 |

- islands n'est pas connexe : un seul chemin est impossible, on renvoie un chemin par île.
- islands contient des arêtes parallèles : il faut identifier les arêtes par leur indice.

## 2. Approche

Pour rendre deux sommets impairs a et b pairs à moindre coût, on duplique les arêtes du
plus court chemin entre a et b : a et b gagnent une arête, les sommets intermédiaires en
gagnent deux et gardent leur parité. Le problème devient un problème de couplage : former
des paires d'impairs en minimisant la somme des distances.

Le couplage exact est trop long à coder en Python, et le MILP ne passe pas à l'échelle sur paris_map (7 318 impairs). 
J'ai donc choisi une heuristique rapide : un glouton, puis une recherche locale. Pour limiter les calculs,
seules les distances entre impairs proches (10 voisins) sont calculées. Un bon couplage relie surtout des sommets proches.

Les étapes :

1. Sommets impairs (`shortest_paths.py`).
2. Distances entre impairs proches : Dijkstra arrêté aux 10 impairs les plus proches (`shortest_paths.py`, `matching.py`).
3. Couplage glouton : paires triées par distance croissante (`matching.py`).
4. Chemin ouvert : retrait de la paire la plus chère de chaque composante, ses 2 sommets deviennent les extrémités.
5. Recherche locale sur le couplage : échange de deux paires, déplacement d'une extrémité.
6. Duplication des arêtes du plus court chemin de chaque paire.
7. Chemin eulérien par composante : Hierholzer itératif (`eulerian.py`), vérifié par `check_path`.

## 3. Validation

- MILP (`milp_solution.py`, PuLP/CBC) : optimum exact sur les petites instances. Sur paris_map, aucune solution trouvée en 10 minutes : le MILP ne passe pas à l'échelle.
- Borne inférieure, pour mesurer la qualité sur paris_map.


Chaque impair doit être relié à un autre impair. Ça coûte au moins la distance à son impair
le plus proche. On additionne pour tous les impairs et on divise par 2, car chaque liaison
a 2 bouts. On enlève les 2 plus grandes valeurs par île, pour les 2 extrémités.

Ces distances sont déjà calculées par Dijkstra, donc la borne ne coûte rien.

## 4. Résultats

| Instance | Coût trouvé | Borne inf. | Optimum MILP | Écart max | Temps |
|---|---|---|---|---|---|
| hard_to_choose | 1200 | 1200 | 1200 | 0 % | < 0,1 s |
| islands | 1914 | 1914 | 1914 | 0 % | < 0,1 s |
| paris_map | 28 987 | 27 305 | non trouvé | 6,2 % | < 1 s |

Sur les deux petites instances, la borne égale le coût trouvé : l'optimalité est prouvée
sans le MILP. Sur paris_map, l'optimum est entre 27 305 et 28 987.

## 5. Code fourni

- `example_solution.py` : `set(graph.edges)` supprime les arêtes parallèles identiques
  (islands : 760 → 706), `if next_vertex:` est faux pour le sommet 0, et le glouton
  s'arrête dès qu'il est bloqué. Non utilisé.
- `main.py` : adapté pour plusieurs chemins, l'affichage de la borne et la comparaison au MILP.
- `input.py` : ajout de l'option `-m`.

## 6. Pistes d'amélioration (TODO)

Par ordre de priorité, si j'avais eu plus de temps :

- Métaheuristique (VNS) sur le couplage, avec des voisinages plus larges (échanges de 3 paires).
- Tester d'autres valeurs du nombre de voisins candidats (10).
- Couplage parfait de poids minimum exact
- Améliorer la borne inférieure (relaxation linéaire du MILP).
