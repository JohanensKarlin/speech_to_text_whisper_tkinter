# =============================================================================
# UI/PLACEMENT.PY – Berechnung der Dialog-Position neben dem Hauptfenster
# =============================================================================
# Reine Logik: Kein Tk. Eingabe = Rechtecke (Parent, Dialog, Bildschirm),
# Ausgabe = (x, y) fuer den Dialog. Reihenfolge: unten, links, oben, rechts;
# jeweils mittig ausgerichtet. Hauptfenster bewegt sich nicht.
# =============================================================================


def place_dialog_beside_parent(
    parent_x: int,
    parent_y: int,
    parent_w: int,
    parent_h: int,
    dialog_w: int,
    dialog_h: int,
    screen_w: int,
    screen_h: int,
    margin: int = 8,
) -> tuple[int, int]:
    """
    Berechnet (dx, dy) so, dass ein Dialog der Groesse (dialog_w, dialog_h)
    neben dem Parent-Rechteck (parent_x, parent_y, parent_w, parent_h) liegt
    und vollstaendig auf dem Bildschirm (0, 0, screen_w, screen_h) bleibt.
    Reihenfolge: unten (mittig), links (mittig), oben, rechts.
    Wenn keine Richtung passt: Bildschirmmitte.
    """
    def fits(dx: int, dy: int) -> bool:
        return (
            dx >= 0 and dy >= 0
            and dx + dialog_w <= screen_w
            and dy + dialog_h <= screen_h
        )

    # Unten: mittig unter Parent
    dx_below = parent_x + (parent_w - dialog_w) // 2
    dy_below = parent_y + parent_h + margin
    if fits(dx_below, dy_below):
        return (dx_below, dy_below)

    # Links: mittig vertikal
    dx_left = parent_x - dialog_w - margin
    dy_left = parent_y + (parent_h - dialog_h) // 2
    if fits(dx_left, dy_left):
        return (dx_left, dy_left)

    # Oben: mittig ueber Parent
    dx_above = parent_x + (parent_w - dialog_w) // 2
    dy_above = parent_y - dialog_h - margin
    if fits(dx_above, dy_above):
        return (dx_above, dy_above)

    # Rechts: mittig vertikal
    dx_right = parent_x + parent_w + margin
    dy_right = parent_y + (parent_h - dialog_h) // 2
    if fits(dx_right, dy_right):
        return (dx_right, dy_right)

    # Fallback: Bildschirmmitte
    return (
        max(0, (screen_w - dialog_w) // 2),
        max(0, (screen_h - dialog_h) // 2),
    )


def get_dialog_position_beside_parent(parent_window, dialog_w: int, dialog_h: int) -> tuple[int, int]:
    """
    Holt Parent-Geometrie und Bildschirmgroesse von parent_window (Tk),
    ruft place_dialog_beside_parent auf. Vorher update_idletasks(), damit
    Position/Groesse aktuell sind.
    """
    parent_window.update_idletasks()
    px = parent_window.winfo_x()
    py = parent_window.winfo_y()
    pw = parent_window.winfo_width()
    ph = parent_window.winfo_height()
    sw = parent_window.winfo_screenwidth()
    sh = parent_window.winfo_screenheight()
    return place_dialog_beside_parent(px, py, pw, ph, dialog_w, dialog_h, sw, sh)
