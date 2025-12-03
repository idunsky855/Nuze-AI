import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from '../App'
import * as api from '../api'

// Mock the api module
vi.mock('../api')

describe('App', () => {
    it('renders articles fetched from api', async () => {
        const mockArticles = [
            { id: 1, title: 'Article 1', content: 'Content 1', author: 'Author 1' },
            { id: 2, title: 'Article 2', content: 'Content 2', author: 'Author 2' },
            { id: 3, title: 'Article 3', content: 'Content 3', author: 'Author 3' },
            { id: 4, title: 'Article 4', content: 'Content 4', author: 'Author 4' },
            { id: 5, title: 'Article 5', content: 'Content 5', author: 'Author 5' },
        ]

        api.fetchArticles.mockResolvedValue(mockArticles)

        render(<App />)

        expect(screen.getByText('Nuze Articles')).toBeInTheDocument()
        expect(screen.getByText('Loading articles...')).toBeInTheDocument()

        await waitFor(() => {
            expect(screen.queryByText('Loading articles...')).not.toBeInTheDocument()
        })

        expect(screen.getByText('Article 1')).toBeInTheDocument()
        expect(screen.getByText('Article 5')).toBeInTheDocument()
        expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(5)
    })
})
