package common

import (
	"errors"
	"net"
	"sync"
)

type Protocol struct {
	serverAddress string
	conn          net.Conn
	running       bool
	mutex         sync.Mutex
}

func NewProtocol(serverAddress string) *Protocol {
	return &Protocol{
		serverAddress: serverAddress,
	}
}

func (p *Protocol) Start() error {
	conn, err := net.Dial("tcp", p.serverAddress)
	if err != nil {
		log.Errorf("action: connect | result: fail | error: %v", err)
		return err
	}
	p.conn = conn
	p.running = true
	log.Infof("action: connect | result: success | server_address: %s", p.serverAddress)
	return nil
}

func (p *Protocol) Stop() error {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	p.running = false
	p.conn.Close()
	return nil
}

func (p *Protocol) sendMessage(message []byte) error {
	nullTerm := []byte{0}
	msg := append(message, nullTerm...)

	// Lock only when sending message
	p.mutex.Lock()
	defer p.mutex.Unlock()

	if !p.running {
		return errors.New("connection closed")
	}
	written := 0
	for written < len(msg) {
		n, err := p.conn.Write(msg[written:])
		if err != nil {
			return err
		}
		written += n
	}
	return nil
}

func serializeSingleBetRequest(request BetRequest) []byte {
	// Convert name to bytes with 2-byte length prefix
	nameBytes := []byte(request.Name)
	nameLen := uint16(len(nameBytes))
	nameLenBytes := []byte{byte(nameLen >> 8), byte(nameLen)}

	// Convert surname to bytes with 2-byte length prefix
	surnameBytes := []byte(request.Surname)
	surnameLen := uint16(len(surnameBytes))
	surnameLenBytes := []byte{byte(surnameLen >> 8), byte(surnameLen)}

	// Convert document number to 4 bytes
	docNum := uint32(request.Document)
	docBytes := []byte{
		byte(docNum >> 24),
		byte(docNum >> 16),
		byte(docNum >> 8),
		byte(docNum),
	}

	// Convert birth date to 4 bytes (2 for year, 1 for month, 1 for day)
	year := uint16(request.Birthdate.Year())
	yearBytes := []byte{byte(year >> 8), byte(year)}
	monthByte := byte(request.Birthdate.Month())
	dayByte := byte(request.Birthdate.Day())

	// Convert bet number to 4 bytes
	betNum := uint32(request.Number)
	betNumBytes := []byte{
		byte(betNum >> 24),
		byte(betNum >> 16),
		byte(betNum >> 8),
		byte(betNum),
	}

	// Combine all parts
	serialized := append(nameLenBytes, nameBytes...)
	serialized = append(serialized, surnameLenBytes...)
	serialized = append(serialized, surnameBytes...)
	serialized = append(serialized, docBytes...)
	serialized = append(serialized, yearBytes...)
	serialized = append(serialized, monthByte)
	serialized = append(serialized, dayByte)
	serialized = append(serialized, betNumBytes...)

	return serialized
}

func (p *Protocol) SendBetRequest(message BetRequest) error {
	// Message type 0 for bet request
	msgType := []byte{1}
	request := serializeSingleBetRequest(message)
	msg := append(msgType, request...)

	return p.sendMessage(msg)
}

func (p *Protocol) SendBetRequestBatch(message BetRequestBatch) error {
	msg := []byte{2}
	numBets := uint16(len(message.Bets))
	numBetsBytes := []byte{byte(numBets >> 8), byte(numBets)}
	msg = append(msg, numBetsBytes...)
	for _, bet := range message.Bets {
		request := serializeSingleBetRequest(bet)
		msg = append(msg, request...)
	}

	return p.sendMessage(msg)
}

func (p *Protocol) SendFinishedBets(message FinishedBets) error {
	msg := []byte{3}

	return p.sendMessage(msg)
}
