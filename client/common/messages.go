package common

import "time"

type BetRequest struct {
	Name      string
	Surname   string
	Birthdate time.Time
	Document  int
	Number    int
}

func (b *BetRequest) size() int {
	return 2 + len(b.Name) + 2 + len(b.Surname) + 4 + 4 + 4
}

type BetRequestBatch struct {
	Agency int
	Bets   []BetRequest
}

// Size of the serialized batch in bytes
func (b *BetRequestBatch) Size() int {
	bets_size := 0
	for _, bet := range b.Bets {
		bets_size += bet.size()
	}
	return 2 + 2 + bets_size
}

type FinishedBets struct {
}
