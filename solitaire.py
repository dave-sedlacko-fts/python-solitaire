#!/usr/bin/env python3
"""
Klondike Solitaire - A classic card game implemented in Python with Pygame
Features drag and drop card movement, standard 52-card deck, and full game rules.
"""

import pygame
import random
import sys
import copy

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
CARD_WIDTH = 80
CARD_HEIGHT = 110
CARD_GAP = 30
TABLEAU_OFFSET = 25  # Vertical offset for stacked cards

# Colors
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
DARK_GREEN = (0, 100, 0)
GOLD = (255, 215, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
CARD_BACK_COLOR = (25, 25, 112)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 149, 237)

# Scoring values
SCORE_TO_FOUNDATION = 10
SCORE_REVEAL_CARD = 5
SCORE_WASTE_TO_TABLEAU = 5
SCORE_FOUNDATION_TO_TABLEAU = -15
SCORE_RECYCLE_WASTE = -20

# Suits and ranks
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
SUIT_SYMBOLS = {'hearts': '♥', 'diamonds': '♦', 'clubs': '♣', 'spades': '♠'}
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RANK_VALUES = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
               '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}


class Card:
    """Represents a playing card."""

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        self.x = 0
        self.y = 0
        self.rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)

    @property
    def color(self):
        """Returns 'red' or 'black' based on suit."""
        return 'red' if self.suit in ['hearts', 'diamonds'] else 'black'

    @property
    def value(self):
        """Returns numerical value of the card."""
        return RANK_VALUES[self.rank]

    def set_position(self, x, y):
        """Set card position."""
        self.x = x
        self.y = y
        self.rect.topleft = (x, y)

    def draw(self, screen):
        """Draw the card on screen."""
        if self.face_up:
            self._draw_face(screen)
        else:
            self._draw_back(screen)

    def _draw_face(self, screen):
        """Draw the front of the card."""
        # Card background
        pygame.draw.rect(screen, WHITE, self.rect, border_radius=8)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=8)

        # Card color
        card_color = RED if self.color == 'red' else BLACK

        # Fonts
        rank_font = pygame.font.Font(None, 28)
        suit_font = pygame.font.Font(None, 36)
        center_font = pygame.font.Font(None, 48)

        # Rank in top-left
        rank_text = rank_font.render(self.rank, True, card_color)
        screen.blit(rank_text, (self.x + 6, self.y + 6))

        # Small suit under rank
        suit_text = suit_font.render(SUIT_SYMBOLS[self.suit], True, card_color)
        screen.blit(suit_text, (self.x + 6, self.y + 24))

        # Large suit in center
        center_suit = center_font.render(SUIT_SYMBOLS[self.suit], True, card_color)
        center_rect = center_suit.get_rect(center=(self.x + CARD_WIDTH // 2,
                                                    self.y + CARD_HEIGHT // 2))
        screen.blit(center_suit, center_rect)

        # Rank in bottom-right (upside down effect)
        rank_text_bottom = rank_font.render(self.rank, True, card_color)
        screen.blit(rank_text_bottom, (self.x + CARD_WIDTH - 20,
                                        self.y + CARD_HEIGHT - 24))

    def _draw_back(self, screen):
        """Draw the back of the card."""
        pygame.draw.rect(screen, CARD_BACK_COLOR, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)

        # Pattern on back
        inner_rect = pygame.Rect(self.x + 8, self.y + 8,
                                  CARD_WIDTH - 16, CARD_HEIGHT - 16)
        pygame.draw.rect(screen, GOLD, inner_rect, 2, border_radius=4)

    def contains_point(self, pos):
        """Check if a point is within the card's bounds."""
        return self.rect.collidepoint(pos)

    def __repr__(self):
        return f"{self.rank} of {self.suit}"


class Deck:
    """Represents a standard 52-card deck."""

    def __init__(self):
        self.cards = []
        self.create_deck()

    def create_deck(self):
        """Create a standard 52-card deck."""
        self.cards = []
        for suit in SUITS:
            for rank in RANKS:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self):
        """Deal one card from the deck."""
        if self.cards:
            return self.cards.pop()
        return None


class Pile:
    """Base class for card piles."""

    def __init__(self, x, y):
        self.cards = []
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)

    def add_card(self, card):
        """Add a card to the pile."""
        self.cards.append(card)
        self.update_positions()

    def add_cards(self, cards):
        """Add multiple cards to the pile."""
        self.cards.extend(cards)
        self.update_positions()

    def remove_card(self):
        """Remove and return the top card."""
        if self.cards:
            card = self.cards.pop()
            self.update_positions()
            return card
        return None

    def remove_cards_from(self, card):
        """Remove a card and all cards on top of it."""
        if card in self.cards:
            index = self.cards.index(card)
            removed = self.cards[index:]
            self.cards = self.cards[:index]
            self.update_positions()
            return removed
        return []

    def top_card(self):
        """Return the top card without removing it."""
        return self.cards[-1] if self.cards else None

    def update_positions(self):
        """Update card positions - override in subclasses."""
        for i, card in enumerate(self.cards):
            card.set_position(self.x, self.y)

    def draw(self, screen):
        """Draw the pile."""
        if not self.cards:
            # Draw empty pile placeholder
            pygame.draw.rect(screen, DARK_GREEN, self.rect, 2, border_radius=8)
        for card in self.cards:
            card.draw(screen)

    def get_card_at(self, pos):
        """Get the topmost card at a position."""
        for card in reversed(self.cards):
            if card.contains_point(pos) and card.face_up:
                return card
        return None


class TableauPile(Pile):
    """A tableau pile where cards are stacked vertically."""

    def update_positions(self):
        """Update positions with vertical offset."""
        for i, card in enumerate(self.cards):
            offset = TABLEAU_OFFSET if card.face_up else TABLEAU_OFFSET // 2
            card.set_position(self.x, self.y + i * offset)

    def can_add(self, card):
        """Check if a card can be added to this pile."""
        if not self.cards:
            # Only kings can be placed on empty tableau
            return card.rank == 'K'

        top = self.top_card()
        if not top.face_up:
            return False

        # Must be opposite color and one rank lower
        if card.color == top.color:
            return False
        if card.value != top.value - 1:
            return False

        return True

    def get_card_at(self, pos):
        """Get the card at position (can be any face-up card)."""
        for card in reversed(self.cards):
            if card.contains_point(pos) and card.face_up:
                return card
        return None

    def flip_top_card(self):
        """Flip the top card face up if face down."""
        if self.cards and not self.cards[-1].face_up:
            self.cards[-1].face_up = True
            self.update_positions()


class FoundationPile(Pile):
    """A foundation pile where cards are stacked by suit."""

    def __init__(self, x, y, suit=None):
        super().__init__(x, y)
        self.suit = suit

    def can_add(self, card):
        """Check if a card can be added to this pile."""
        if not self.cards:
            # Only aces can start a foundation
            return card.rank == 'A'

        top = self.top_card()
        # Must be same suit and one rank higher
        if card.suit != top.suit:
            return False
        if card.value != top.value + 1:
            return False

        return True

    def draw(self, screen):
        """Draw foundation with suit indicator."""
        if not self.cards:
            pygame.draw.rect(screen, DARK_GREEN, self.rect, 2, border_radius=8)
            # Draw suit symbol placeholder if suit assigned
            if self.suit:
                font = pygame.font.Font(None, 36)
                color = GRAY
                text = font.render(SUIT_SYMBOLS[self.suit], True, color)
                text_rect = text.get_rect(center=(self.x + CARD_WIDTH // 2,
                                                   self.y + CARD_HEIGHT // 2))
                screen.blit(text, text_rect)
        else:
            self.top_card().draw(screen)


class StockPile(Pile):
    """The stock pile (draw pile)."""

    def draw(self, screen):
        """Draw stock pile."""
        if not self.cards:
            # Draw empty circle to indicate click area for reset
            pygame.draw.rect(screen, DARK_GREEN, self.rect, 2, border_radius=8)
            font = pygame.font.Font(None, 36)
            text = font.render("↺", True, LIGHT_GRAY)
            text_rect = text.get_rect(center=(self.x + CARD_WIDTH // 2,
                                               self.y + CARD_HEIGHT // 2))
            screen.blit(text, text_rect)
        else:
            # Just draw the back of the top card
            self.top_card().draw(screen)


class WastePile(Pile):
    """The waste pile (where drawn cards go)."""

    def draw(self, screen):
        """Draw waste pile - show top card face up."""
        if not self.cards:
            pygame.draw.rect(screen, DARK_GREEN, self.rect, 2, border_radius=8)
        else:
            # Only draw the top card
            self.top_card().draw(screen)


class Solitaire:
    """Main Solitaire game class."""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Klondike Solitaire")
        self.clock = pygame.time.Clock()

        # Game state
        self.running = True
        self.won = False
        self.score = 0
        self.move_history = []  # For undo functionality

        # Drag state
        self.dragging = False
        self.dragged_cards = []
        self.drag_source = None
        self.drag_offset = (0, 0)

        # Undo button
        self.undo_button_rect = pygame.Rect(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 45, 80, 35)

        # Initialize piles
        self.setup_piles()
        self.new_game()

    def setup_piles(self):
        """Set up all the pile positions."""
        # Stock and waste piles (top left)
        self.stock = StockPile(50, 50)
        self.waste = WastePile(50 + CARD_WIDTH + CARD_GAP, 50)

        # Foundation piles (top right)
        self.foundations = []
        foundation_start_x = SCREEN_WIDTH - (4 * (CARD_WIDTH + CARD_GAP)) + CARD_GAP
        for i, suit in enumerate(SUITS):
            x = foundation_start_x + i * (CARD_WIDTH + CARD_GAP)
            self.foundations.append(FoundationPile(x, 50, suit))

        # Tableau piles (bottom)
        self.tableaus = []
        tableau_start_x = 50
        for i in range(7):
            x = tableau_start_x + i * (CARD_WIDTH + CARD_GAP + 10)
            self.tableaus.append(TableauPile(x, 200))

    def new_game(self):
        """Start a new game."""
        self.won = False
        self.score = 0
        self.move_history = []

        # Clear all piles
        self.stock.cards = []
        self.waste.cards = []
        for f in self.foundations:
            f.cards = []
        for t in self.tableaus:
            t.cards = []

        # Create and shuffle deck
        deck = Deck()
        deck.shuffle()

        # Deal to tableau
        for i in range(7):
            for j in range(i, 7):
                card = deck.deal()
                card.face_up = (i == j)  # Only top card face up
                self.tableaus[j].add_card(card)

        # Remaining cards go to stock
        while deck.cards:
            card = deck.deal()
            card.face_up = False
            self.stock.add_card(card)

    def save_state(self):
        """Save the current game state for undo."""
        state = {
            'score': self.score,
            'stock': [(c.suit, c.rank, c.face_up) for c in self.stock.cards],
            'waste': [(c.suit, c.rank, c.face_up) for c in self.waste.cards],
            'foundations': [[(c.suit, c.rank, c.face_up) for c in f.cards] for f in self.foundations],
            'tableaus': [[(c.suit, c.rank, c.face_up) for c in t.cards] for t in self.tableaus]
        }
        self.move_history.append(state)
        # Limit history to prevent memory issues
        if len(self.move_history) > 100:
            self.move_history.pop(0)

    def undo(self):
        """Undo the last move."""
        if not self.move_history:
            return False

        state = self.move_history.pop()
        self.score = state['score']

        # Restore stock
        self.stock.cards = []
        for suit, rank, face_up in state['stock']:
            card = Card(suit, rank)
            card.face_up = face_up
            self.stock.cards.append(card)
        self.stock.update_positions()

        # Restore waste
        self.waste.cards = []
        for suit, rank, face_up in state['waste']:
            card = Card(suit, rank)
            card.face_up = face_up
            self.waste.cards.append(card)
        self.waste.update_positions()

        # Restore foundations
        for i, foundation_state in enumerate(state['foundations']):
            self.foundations[i].cards = []
            for suit, rank, face_up in foundation_state:
                card = Card(suit, rank)
                card.face_up = face_up
                self.foundations[i].cards.append(card)
            self.foundations[i].update_positions()

        # Restore tableaus
        for i, tableau_state in enumerate(state['tableaus']):
            self.tableaus[i].cards = []
            for suit, rank, face_up in tableau_state:
                card = Card(suit, rank)
                card.face_up = face_up
                self.tableaus[i].cards.append(card)
            self.tableaus[i].update_positions()

        self.won = False
        return True

    def add_score(self, points):
        """Add points to score (can be negative)."""
        self.score = max(0, self.score + points)

    def draw_card_from_stock(self):
        """Draw a card from stock to waste."""
        self.save_state()
        if self.stock.cards:
            card = self.stock.remove_card()
            card.face_up = True
            self.waste.add_card(card)
        elif self.waste.cards:
            # Reset: move all waste cards back to stock
            self.add_score(SCORE_RECYCLE_WASTE)
            while self.waste.cards:
                card = self.waste.remove_card()
                card.face_up = False
                self.stock.add_card(card)

    def get_pile_at(self, pos):
        """Get the pile at a position."""
        # Check stock
        if self.stock.rect.collidepoint(pos):
            return self.stock

        # Check waste
        if self.waste.cards:
            if self.waste.top_card().contains_point(pos):
                return self.waste
        elif self.waste.rect.collidepoint(pos):
            return self.waste

        # Check foundations
        for f in self.foundations:
            if f.cards:
                if f.top_card().contains_point(pos):
                    return f
            elif f.rect.collidepoint(pos):
                return f

        # Check tableaus (check from bottom of each pile)
        for t in self.tableaus:
            for card in reversed(t.cards):
                if card.contains_point(pos):
                    return t
            if not t.cards and t.rect.collidepoint(pos):
                return t

        return None

    def handle_click(self, pos):
        """Handle mouse click."""
        pile = self.get_pile_at(pos)

        if pile == self.stock:
            self.draw_card_from_stock()
            return

        if pile and pile.cards:
            card = pile.get_card_at(pos)
            if card:
                self.start_drag(pile, card, pos)

    def start_drag(self, pile, card, pos):
        """Start dragging cards."""
        if isinstance(pile, WastePile):
            self.dragged_cards = [pile.top_card()]
        elif isinstance(pile, FoundationPile):
            self.dragged_cards = [pile.top_card()]
        elif isinstance(pile, TableauPile):
            self.dragged_cards = pile.remove_cards_from(card)
            pile.add_cards(self.dragged_cards)  # Temporarily add back
        else:
            return

        if self.dragged_cards:
            self.dragging = True
            self.drag_source = pile
            self.drag_offset = (pos[0] - self.dragged_cards[0].x,
                               pos[1] - self.dragged_cards[0].y)

    def handle_drag(self, pos):
        """Handle mouse drag."""
        if self.dragging and self.dragged_cards:
            base_x = pos[0] - self.drag_offset[0]
            base_y = pos[1] - self.drag_offset[1]

            for i, card in enumerate(self.dragged_cards):
                card.set_position(base_x, base_y + i * TABLEAU_OFFSET)

    def handle_drop(self, pos):
        """Handle mouse release (drop)."""
        if not self.dragging:
            return

        self.dragging = False

        # Find valid drop target
        drop_target = self.find_drop_target(pos)

        if drop_target and drop_target != self.drag_source:
            # Save state before making the move
            self.save_state()

            # Check if we need to flip a card (for scoring)
            will_flip = (isinstance(self.drag_source, TableauPile) and
                        len(self.drag_source.cards) > len(self.dragged_cards) and
                        not self.drag_source.cards[-(len(self.dragged_cards) + 1)].face_up)

            # Valid drop - move cards
            if isinstance(self.drag_source, TableauPile):
                self.drag_source.remove_cards_from(self.dragged_cards[0])
            else:
                for _ in self.dragged_cards:
                    self.drag_source.remove_card()

            drop_target.add_cards(self.dragged_cards)

            # Calculate score
            if isinstance(drop_target, FoundationPile):
                self.add_score(SCORE_TO_FOUNDATION * len(self.dragged_cards))
            elif isinstance(drop_target, TableauPile):
                if isinstance(self.drag_source, WastePile):
                    self.add_score(SCORE_WASTE_TO_TABLEAU)
                elif isinstance(self.drag_source, FoundationPile):
                    self.add_score(SCORE_FOUNDATION_TO_TABLEAU)

            # Flip top card of source tableau if needed
            if isinstance(self.drag_source, TableauPile):
                if self.drag_source.cards and not self.drag_source.cards[-1].face_up:
                    self.drag_source.flip_top_card()
                    self.add_score(SCORE_REVEAL_CARD)
        else:
            # Invalid drop - return cards to source
            self.drag_source.update_positions()

        self.dragged_cards = []
        self.drag_source = None

        # Check for win
        self.check_win()

    def find_drop_target(self, pos):
        """Find a valid drop target for the dragged cards."""
        if not self.dragged_cards:
            return None

        first_card = self.dragged_cards[0]

        # Check foundations (only single cards)
        if len(self.dragged_cards) == 1:
            for f in self.foundations:
                # Check if hovering over foundation area
                expanded_rect = pygame.Rect(f.x - 20, f.y - 20,
                                           CARD_WIDTH + 40, CARD_HEIGHT + 40)
                if expanded_rect.collidepoint(pos) and f.can_add(first_card):
                    return f

        # Check tableaus
        for t in self.tableaus:
            # Get the drop zone (bottom of pile or pile area if empty)
            if t.cards:
                top_card = t.top_card()
                expanded_rect = pygame.Rect(top_card.x - 20, top_card.y - 20,
                                           CARD_WIDTH + 40, CARD_HEIGHT + 60)
            else:
                expanded_rect = pygame.Rect(t.x - 20, t.y - 20,
                                           CARD_WIDTH + 40, CARD_HEIGHT + 40)

            if expanded_rect.collidepoint(pos) and t.can_add(first_card):
                return t

        return None

    def check_win(self):
        """Check if the player has won."""
        for f in self.foundations:
            if len(f.cards) != 13:
                return
        self.won = True

    def auto_move_to_foundation(self):
        """Automatically move cards to foundations if possible."""
        # Save state before auto-complete
        self.save_state()

        moved = True
        while moved:
            moved = False

            # Check waste
            if self.waste.cards:
                card = self.waste.top_card()
                for f in self.foundations:
                    if f.can_add(card):
                        self.waste.remove_card()
                        f.add_card(card)
                        self.add_score(SCORE_TO_FOUNDATION)
                        moved = True
                        break

            # Check tableaus
            for t in self.tableaus:
                if t.cards:
                    card = t.top_card()
                    for f in self.foundations:
                        if f.can_add(card):
                            t.remove_card()
                            f.add_card(card)
                            self.add_score(SCORE_TO_FOUNDATION)
                            if t.cards and not t.cards[-1].face_up:
                                t.flip_top_card()
                                self.add_score(SCORE_REVEAL_CARD)
                            moved = True
                            break
                    if moved:
                        break

        self.check_win()

    def draw(self):
        """Draw the game."""
        self.screen.fill(GREEN)

        # Draw piles
        self.stock.draw(self.screen)
        self.waste.draw(self.screen)

        for f in self.foundations:
            f.draw(self.screen)

        for t in self.tableaus:
            t.draw(self.screen)

        # Draw dragged cards on top
        if self.dragging:
            for card in self.dragged_cards:
                card.draw(self.screen)

        # Draw UI
        self.draw_ui()

        # Draw win message
        if self.won:
            self.draw_win_message()

        pygame.display.flip()

    def draw_ui(self):
        """Draw UI elements."""
        font = pygame.font.Font(None, 28)
        score_font = pygame.font.Font(None, 36)

        # Score display (top center)
        score_text = score_font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 25))
        self.screen.blit(score_text, score_rect)

        # Undo button
        mouse_pos = pygame.mouse.get_pos()
        button_color = BUTTON_HOVER_COLOR if self.undo_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        if not self.move_history:
            button_color = GRAY  # Disabled appearance

        pygame.draw.rect(self.screen, button_color, self.undo_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, self.undo_button_rect, 2, border_radius=5)

        undo_text = font.render("Undo", True, WHITE)
        undo_rect = undo_text.get_rect(center=self.undo_button_rect.center)
        self.screen.blit(undo_text, undo_rect)

        # Moves counter (next to undo button)
        moves_text = font.render(f"Moves: {len(self.move_history)}", True, WHITE)
        self.screen.blit(moves_text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 38))

        # Instructions
        instructions = [
            "Click stock to draw | Double-click to auto-move | 'U' to undo",
            "Press 'N' for new game | Press 'A' to auto-complete | Press 'Q' to quit"
        ]

        y = SCREEN_HEIGHT - 50
        for text in instructions:
            surface = font.render(text, True, WHITE)
            rect = surface.get_rect(center=(SCREEN_WIDTH // 2 - 80, y))
            self.screen.blit(surface, rect)
            y += 25

    def draw_win_message(self):
        """Draw the winning message."""
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        # Win text
        font = pygame.font.Font(None, 72)
        text = font.render("You Win!", True, GOLD)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(text, rect)

        # Instructions
        font_small = pygame.font.Font(None, 36)
        text2 = font_small.render("Press 'N' for new game or 'Q' to quit", True, WHITE)
        rect2 = text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(text2, rect2)

    def run(self):
        """Main game loop."""
        last_click_time = 0
        last_click_pos = (0, 0)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # Check for undo button click
                        if self.undo_button_rect.collidepoint(event.pos):
                            self.undo()
                            continue

                        current_time = pygame.time.get_ticks()

                        # Check for double click
                        if (current_time - last_click_time < 300 and
                            abs(event.pos[0] - last_click_pos[0]) < 10 and
                            abs(event.pos[1] - last_click_pos[1]) < 10):
                            # Double click - try auto move
                            pile = self.get_pile_at(event.pos)
                            if pile and pile.cards and not isinstance(pile, (StockPile, FoundationPile)):
                                card = pile.top_card()
                                for f in self.foundations:
                                    if f.can_add(card):
                                        self.save_state()
                                        pile.remove_card()
                                        f.add_card(card)
                                        self.add_score(SCORE_TO_FOUNDATION)
                                        if isinstance(pile, TableauPile):
                                            if pile.cards and not pile.cards[-1].face_up:
                                                pile.flip_top_card()
                                                self.add_score(SCORE_REVEAL_CARD)
                                        self.check_win()
                                        break
                        else:
                            self.handle_click(event.pos)

                        last_click_time = current_time
                        last_click_pos = event.pos

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        self.handle_drag(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_drop(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        self.new_game()
                    elif event.key == pygame.K_q:
                        self.running = False
                    elif event.key == pygame.K_a:
                        self.auto_move_to_foundation()
                    elif event.key == pygame.K_u:
                        self.undo()
                    elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.undo()

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
    """Entry point."""
    game = Solitaire()
    game.run()


if __name__ == "__main__":
    main()
