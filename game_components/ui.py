import pygame
import game_components.shared as _s


# Helpers ─────────────────────────────────────────────────────────────────
def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


def glow_text(surf, font, text, color, cx, cy, glow_r=3):
    """Render text with a soft halo."""
    glow_col = tuple(max(0, c//4) for c in color)
    for dx in range(-glow_r, glow_r+1, glow_r):
        for dy in range(-glow_r, glow_r+1, glow_r):
            if dx == 0 and dy == 0: continue
            t = font.render(text, True, glow_col)
            surf.blit(t, (cx - t.get_width()//2 + dx, cy - t.get_height()//2 + dy))
    t = font.render(text, True, color)
    surf.blit(t, (cx - t.get_width()//2, cy - t.get_height()//2))
    return t.get_width(), t.get_height()


def draw_panel(surf, rect, border_col=None, radius=10):
    pygame.draw.rect(surf, _s.C['panel'], rect, border_radius=radius)
    pygame.draw.rect(surf, border_col or _s.C['border'], rect, 1, border_radius=radius)


# Button ───────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, label, cx, cy, w=320, h=58,
                 color_key='red', disabled=False):
        self.label    = label
        self.rect     = pygame.Rect(cx - w//2, cy - h//2, w, h)
        self.ck       = color_key
        self.disabled = disabled
        self._hover_t = 0.0

    def update(self, mouse):
        target = 1.0 if (self.rect.collidepoint(mouse) and not self.disabled) else 0.0
        self._hover_t += (target - self._hover_t) * 0.18

    def clicked(self, mouse):
        return (not self.disabled) and self.rect.collidepoint(mouse)

    def draw(self, surf):
        t  = self._hover_t
        fg = _s.C[self.ck]
        bg_col = lerp_color(_s.C['panel'], tuple(max(0, c//5) for c in fg), t*0.4)
        br_col = lerp_color(_s.C['border'], fg, t)
        tx_col = lerp_color(_s.C['dim'], _s.C['white'], t) if not self.disabled else _s.C['dim']

        # Glow behind hovered button
        if t > 0.05:
            glow = pygame.Surface((self.rect.w + 30, self.rect.h + 30), pygame.SRCALPHA)
            gr = pygame.Rect(0, 0, self.rect.w+30, self.rect.h+30)
            pygame.draw.rect(glow, (*fg, int(35*t)), gr, border_radius=14)
            surf.blit(glow, (self.rect.x-15, self.rect.y-15))

        pygame.draw.rect(surf, bg_col, self.rect, border_radius=8)
        pygame.draw.rect(surf, br_col, self.rect, 2, border_radius=8)

        # Left accent bar
        bar_col = lerp_color(_s.C['border'], fg, t)
        pygame.draw.rect(surf, bar_col,
                         (self.rect.x, self.rect.y+10, 3, self.rect.h-20),
                         border_radius=2)

        txt = _s.F_MED.render(self.label, True, tx_col)
        surf.blit(txt, (self.rect.centerx - txt.get_width()//2,
                        self.rect.centery - txt.get_height()//2))

        if self.disabled:
            ds = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            ds.fill((0, 0, 0, 80))
            surf.blit(ds, self.rect.topleft)
            tag = _s.F_XSM.render("COMING SOON", True, _s.C['dim'])
            surf.blit(tag, (self.rect.right - tag.get_width() - 10,
                            self.rect.bottom - tag.get_height() - 6))
