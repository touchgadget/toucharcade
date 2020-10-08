import os
import pygame

class TouchAreas:
    def __init__(self, topLeft, bottomRight, rows, columns, gridlines, bgcolor, font, properties, displaysurf):
        """ Constructor """
        self.topLeft = topLeft
        self.bottomRight = bottomRight
        self.rows = rows
        self.columns = columns
        self.gridLines = gridlines
        self.bgcolor = bgcolor
        self.cells = []
        self.cell_height = (bottomRight[1] - topLeft[1]) / rows
        self.cell_width = (bottomRight[0] - topLeft[0]) / columns
        self.font = font
        self.cell_properties = properties
        self.displaysurf = displaysurf
        (self.screen_width, self.screen_height) = displaysurf.get_size()
        self.screen_width_max = self.screen_width - 1     # Max pixel co-ord
        self.screen_height_max = self.screen_height -1    # Max pixel co-ord

    def drawCell(self, gridcell, color):
        """ Draw one cell """
        rect = gridcell['rect']
        pygame.draw.rect(self.displaysurf, color, rect, 0)
        picture = gridcell.get('picture')
        if picture:
            self.displaysurf.blit(picture, rect)
        text = gridcell.get('text')
        textpos = gridcell.get('textpos')
        if text and textpos:
            self.displaysurf.blit(text, textpos)
        pygame.display.update(rect)

    def draw(self):
        """
        Draw all buttons. Usually called only once.
        Draw grid of size width x height. Each element of the grid is a cell of
        cell_width x cell_height. For example, given a screen size of 1920 x 1080 and a grid 32 cols and 1
        row, cell_width = 1920 / 32 and cell_height = 1080 / 1
        """
        cell_index = 0
        for y in range(self.rows):
            for x in range(self.columns):
                gridcell = {}
                gridcell['myself'] = self
                gridcell["buttonDown"] = 0
                rect = pygame.Rect(self.topLeft[0] + x*self.cell_width,
                        self.topLeft[1] + y*self.cell_height,
                        self.cell_width, self.cell_height)
                gridcell["rect"] = rect
                cell_center = (self.topLeft[0] + int(x * self.cell_width + self.cell_width/2),
                    self.topLeft[1] + int(y * self.cell_height + self.cell_height/2))
                gridcell["button_center"] = cell_center
                if self.cell_properties:
                    props= self.cell_properties[cell_index]
                    if props.get('label') != None:
                        text = self.font.render(props['label'], 1, (10, 10, 10))
                        textpos = text.get_rect(center=cell_center)
                        gridcell['text'] = text
                        gridcell['textpos'] = textpos
                        self.displaysurf.blit(text, textpos)
                    if props.get('picture') != None:
                        gridcell['picture'] = pygame.image.load(os.path.join('assets', props['picture']))
                    gridcell['color'] = props.get('buttonColor', self.bgcolor)
                    self.drawCell(gridcell, gridcell['color'])
                    if props.get('button') != None:
                        gridcell['button'] = props['button']
                gridcell['index'] = cell_index
                self.cells.append(gridcell)
                cell_index = cell_index + 1
            if self.gridLines:
                # Draw horizontal grid lines
                pygame.draw.line(self.displaysurf, (0, 0, 0),
                        (0, y*self.cell_height), (self.screen_width_max, y*self.cell_height))
        if self.gridLines:
            # Draw vertical grid lines
            for x in range(self.columns):
                pygame.draw.line(self.displaysurf, (0, 0, 0),
                        (x*self.cell_width, self.topLeft[1]), (x*self.cell_width, self.bottomRight[1]))
    
    def buttonOn(self, gridcell):
        """ Button touched/pressed """
        gridcell['buttonDown'] += 1
        return (gridcell['buttonDown'] == 1)

    def buttonOff(self, gridcell):
        """ Button released """
        gridcell['buttonDown'] -= 1
        if gridcell['buttonDown'] < 0:
            gridcell['buttonDown'] = 0
        return (gridcell['buttonDown'] == 0)

    def touchToCell(self, x, y):
        """ Convert touch co-ordinates to cell array offset """
        x = int(x)
        y = int(y)
        if (x >= self.topLeft[0]) and (x <= self.bottomRight[0]) and (y >= self.topLeft[1]) and (y <= self.bottomRight[1]):
            x = int(x / self.cell_width)
            if x >= self.columns:
                x = self.columns-1
            y = int(y / self.cell_height)
            if y >= self.rows:
                y = self.rows - 1
            return self.cells[y*(self.rows-1) + x]
        return -1
