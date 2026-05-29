import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  TextField,
  IconButton,
  Typography,
  AppBar,
  Toolbar,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  InputAdornment,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import LogoutIcon from '@mui/icons-material/Logout';
import ForumIcon from '@mui/icons-material/Forum';
import AddIcon from '@mui/icons-material/Add';
import LoginIcon from '@mui/icons-material/Login';
import { useNavigate } from 'react-router-dom';
import api from '../api';

interface ChatMessage {
  sender: string;
  text: string;
  is_system: boolean;
}

interface Room {
  id: number;
  name: string;
}

const Chat: React.FC = () => {
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || '';

  const [rooms, setRooms] = useState<Room[]>([]); 
  const [activeRoom, setActiveRoom] = useState<number>(1);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [joinRoomIdInput, setJoinRoomIdInput] = useState('');

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchRooms = async () => {
    try {
      const response = await api.get<Room[]>('/rooms');
      setRooms(response.data);
    } catch (error) {
      console.error('Error fetching rooms:', error);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  useEffect(() => {
    if (!username || rooms.length === 0) return;

    let isMounted = true;
    const wsUrl = `ws://${window.location.host}/ws/${activeRoom}`;
    let ws: WebSocket | null = null;

    const loadHistoryAndConnect = async () => {
      try {
        const response = await api.get<ChatMessage[]>(`/rooms/${activeRoom}/messages`);
        if (isMounted) {
          setMessages(response.data);

          ws = new WebSocket(wsUrl);
          wsRef.current = ws;

          ws.onmessage = (event) => {
            if (isMounted) {
              const incomingMessage: ChatMessage = JSON.parse(event.data);
              setMessages((prev) => [...prev, incomingMessage]);
            }
          };

          ws.onclose = () => {
            console.log('WebSocket connection closed');
          };
        }
      } catch (error) {
        console.error('Error loading message history:', error);
        if (isMounted) {
          setMessages([
            { sender: 'System', text: `Error: Room with ID ${activeRoom} was not found in the database.`, is_system: true }
          ]);
        }
      }
    };

    loadHistoryAndConnect();

    return () => {
      isMounted = false;
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close();
      }
    };
  }, [activeRoom, username, rooms]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !wsRef.current) return;

    if (wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text: inputText }));
      setInputText('');
    }
  };

  const handleCreateRoom = async () => {
    if (!newRoomName.trim()) return;
    try {
      const response = await api.post<Room>('/rooms', { name: newRoomName });
      setNewRoomName('');
      setOpenCreateDialog(false);
      await fetchRooms();
      setActiveRoom(response.data.id);
    } catch (error) {
      console.error('Failed to create room:', error);
    }
  };

  const handleJoinById = (e: React.FormEvent) => {
    e.preventDefault();
    const id = parseInt(joinRoomIdInput);
    if (isNaN(id)) return;

    setActiveRoom(id);
    setJoinRoomIdInput('');
  };

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      console.error('Error logging out', e);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
    localStorage.clear();
    navigate('/login');
  };

  const activeRoomName = rooms.find(r => r.id === activeRoom)?.name || `Room #${activeRoom}`;

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static">
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ForumIcon />
            <Typography variant="h6">RTChat</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="subtitle1">Logged in as: <b>{username}</b></Typography>
            <Button 
              color="inherit" 
              variant="outlined" 
              startIcon={<LogoutIcon />} 
              onClick={handleLogout}
              size="small"
            >
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        
        <Box 
          component={Paper} 
          elevation={1} 
          square 
          sx={{ 
            width: { xs: '220px', sm: '280px', md: '320px' },
            flexShrink: 0,
            borderRight: '1px solid #e0e0e0', 
            display: 'flex', 
            flexDirection: 'column',
            bgcolor: '#ffffff'
          }}
        >
          <Box sx={{ p: 2 }}>
            <Button 
              fullWidth 
              variant="contained" 
              color="primary" 
              startIcon={<AddIcon />}
              onClick={() => setOpenCreateDialog(true)}
            >
              Create Room
            </Button>
          </Box>
          
          <Divider />

          <Box component="form" onSubmit={handleJoinById} sx={{ p: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Join Room by ID"
              value={joinRoomIdInput}
              onChange={(e) => setJoinRoomIdInput(e.target.value)}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton size="small" type="submit">
                        <LoginIcon fontSize="small" />
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />
          </Box>

          <Divider />

          <Typography variant="subtitle2" color="textSecondary" sx={{ px: 2, pt: 2, pb: 1 }}>
            Available Chats
          </Typography>
          <List sx={{ flexGrow: 1, overflowY: 'auto' }}>
            {rooms.map((room) => (
              <ListItem key={room.id} disablePadding>
                <ListItemButton 
                  selected={activeRoom === room.id} 
                  onClick={() => setActiveRoom(room.id)}
                >
                  <ListItemText 
                    primary={room.name} 
                    secondary={`ID: ${room.id}`}
                    slotProps={{
                      secondary: {
                        sx: { fontSize: '0.75rem' }, 
                      },
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>

        <Box 
          sx={{ 
            flexGrow: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            height: '100%', 
            bgcolor: '#f5f5f5' 
          }}
        >
          <Box sx={{ p: 2, bgcolor: '#ffffff', borderBottom: '1px solid #e0e0e0' }}>
            <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
              {activeRoomName}
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 3, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {messages.map((msg, index) => {
              if (msg.is_system) {
                return (
                  <Typography 
                    key={index} 
                    variant="caption" 
                    align="center" 
                    color="textSecondary" 
                    sx={{ my: 1, fontStyle: 'italic' }}
                  >
                    {msg.text}
                  </Typography>
                );
              }

              const isMe = msg.sender === username;

              return (
                <Box 
                  key={index} 
                  sx={{ 
                    display: 'flex', 
                    justifyContent: isMe ? 'flex-end' : 'flex-start' 
                  }}
                >
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 1.5, 
                      maxWidth: '70%', 
                      borderRadius: 2,
                      bgcolor: isMe ? '#1976d2' : '#ffffff',
                      color: isMe ? '#ffffff' : '#000000'
                    }}
                  >
                    {!isMe && (
                      <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5, color: '#e64a19' }}>
                        {msg.sender}
                      </Typography>
                    )}
                    <Typography variant="body1" sx={{ wordBreak: 'break-word' }}>
                      {msg.text}
                    </Typography>
                  </Paper>
                </Box>
              );
            })}
            <div ref={messagesEndRef} />
          </Box>

          <Divider />

          <Box 
            component="form" 
            onSubmit={handleSendMessage} 
            sx={{ p: 2, bgcolor: '#ffffff', display: 'flex', gap: 1, alignItems: 'center' }}
          >
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Type a message..."
              size="small"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <IconButton type="submit" color="primary" disabled={!inputText.trim()}>
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Box>

      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)}>
        <DialogTitle>Create a New Room</DialogTitle>
        <DialogContent sx={{ minWidth: '300px', pt: 1 }}>
          <TextField
            autoFocus
            margin="dense"
            label="Room Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newRoomName}
            onChange={(e) => setNewRoomName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateRoom} variant="contained" disabled={!newRoomName.trim()}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Chat;