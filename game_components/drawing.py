import pygame, math
import game_components.shared as _s
from game_components.ui import draw_panel


# Car Preview ─────────────────────────────────────────────────────────
def draw_car_preview(surf, cx, cy, scale=3.0, angle=0,
                     body_col=(210,30,30), accent_col=(255,200,0)):
    L = int(26 * scale)
    Ww = int(13 * scale)
    rad = math.radians(angle)
    ca, sa = math.cos(rad), math.sin(rad)

    def rot(px, py):
        return (int(cx + px*ca - py*sa), int(cy + px*sa + py*ca))

    # Shadow
    shadow = [rot(px+int(3*scale), py+int(3*scale)) for px,py in [
        (-L//2,-Ww//2),(L//2,-Ww//2),(L//2+int(5*scale),0),(L//2,Ww//2),(-L//2,Ww//2)]]
    pygame.draw.polygon(surf, (0,0,0), shadow)

    body = [rot(-L//2,-Ww//2), rot(L//2,-Ww//2),
            rot(L//2+int(5*scale),0), rot(L//2,Ww//2), rot(-L//2,Ww//2)]
    pygame.draw.polygon(surf, body_col, body)
    pygame.draw.polygon(surf, (0,0,0), body, 2)

    roof = [rot(-L//4,-Ww//3), rot(L//4,-Ww//3), rot(L//4,Ww//3), rot(-L//4,Ww//3)]
    pygame.draw.polygon(surf, (160,210,240), roof)

    stripe = [rot(-L//2,-int(2*scale)), rot(L//2+int(5*scale),-int(2*scale)),
              rot(L//2+int(5*scale), int(2*scale)), rot(-L//2, int(2*scale))]
    pygame.draw.polygon(surf, accent_col, stripe)

    for sign in (-1,1):
        hx = cx + (L//2+int(6*scale))*ca - sign*(Ww//3)*sa
        hy = cy + (L//2+int(6*scale))*sa + sign*(Ww//3)*ca
        pygame.draw.circle(surf, (255,255,200), (int(hx), int(hy)), int(3*scale))
    for sign in (-1,1):
        rx = cx + (-L//2-int(2*scale))*ca - sign*(Ww//3)*sa
        ry = cy + (-L//2-int(2*scale))*sa + sign*(Ww//3)*ca
        pygame.draw.circle(surf, (200,40,40), (int(rx), int(ry)), int(3*scale))


# Track Preview ────────────────────────────────────────────────────────────
def draw_track_minimap(surf, rect, waypoints, track_name="CIRCUIT 01"):
    draw_panel(surf, rect.inflate(4,4), _s.C['cyan_dim'], radius=12)
    draw_panel(surf, rect, _s.C['cyan'], radius=10)

    if not waypoints:
        t = _s.F_SM.render("NO TRACK DATA", True, _s.C['dim'])
        surf.blit(t, (rect.centerx - t.get_width()//2, rect.centery))
        return

    xs = [p[0] for p in waypoints]
    ys = [p[1] for p in waypoints]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    pad = 22
    span_x = (mx_x - mn_x) or 1
    span_y = (mx_y - mn_y) or 1

    def proj(p):
        nx = (p[0]-mn_x)/span_x * (rect.w - pad*2) + rect.x + pad
        ny = (p[1]-mn_y)/span_y * (rect.h - pad*2) + rect.y + pad
        return (int(nx), int(ny))

    pts = [proj(p) for p in waypoints]

    # Track body (thick white)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i+1)%len(pts)]
        pygame.draw.line(surf, _s.C['border'], a, b, 9)
    # Centre line (cyan)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i+1)%len(pts)]
        pygame.draw.line(surf, _s.C['cyan'], a, b, 2)
    # Start dot
    pygame.draw.circle(surf, _s.C['red'], pts[0], 6)

    t = _s.F_XSM.render(track_name, True, _s.C['cyan'])
    surf.blit(t, (rect.x + 8, rect.y + 6))
