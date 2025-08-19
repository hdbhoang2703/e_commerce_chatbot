import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Plus, Trash2, MessageSquare, X, Link, Settings } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = import.meta.env.VITE_API_URL;

function App() {
  const [chats, setChats] = useState([
    {
      id: 1,
      title: "Hướng dẫn sử dụng",
      messages: [
        { 
          sender: "bot", 
          text: `**Chào mừng bạn đến với AI Shopping Assistant!**

Tôi là trợ lý mua sắm thông minh, có thể giúp bạn:

**Các tính năng chính:**
- Tư vấn sản phẩm chi tiết.
- Đánh giá ưu nhược điểm từ các đánh giá của khách hàng đã mua sản phẩm.
- Giúp bạn tổng hợp các phản hồi của khách hàng qua đó giúp bạn biết tình trạng thực tế của sản phẩm mà không cần phải đi đọc từng bình luận.

**Cách sử dụng:**
- 1. Nhấn nút **"Chat mới"** ở sidebar
- 2. Dán link sản phẩm từ các trang thương mại điện tử
- 3. Chờ tôi lấy thông tin sản phẩm
- 4. Bắt đầu hỏi bất cứ điều gì về sản phẩm!

**Ví dụ câu hỏi:**
- "Thông số của sản phẩm"
- "Sản phẩm bị khách hàng đánh giá tiêu cực ở điểm nào?"
- "Cho tôi vài hình ảnh sản phẩm từ khách hàng"
- "Tai nghe có bị rè không?"
- "Bình có thể giữ nhiệt trong bao lâu?"
- "Các chính sách bảo hành của sản phẩm như nào?"

Hãy tạo chat mới với link sản phẩm để bắt đầu nhé!`,
          timestamp: new Date()
        }
      ],
      createdAt: new Date(),
      session_id: null,
      product_id: null,
      isGuide: true
    }
  ]);
  
  const [activeChat, setActiveChat] = useState(1);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [linkInput, setLinkInput] = useState("");
  const [isCreatingChat, setIsCreatingChat] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);

  // Use in-memory storage instead of localStorage
  const [savedChats, setSavedChats] = useState(null);

  useEffect(() => {
    // Simulate loading from localStorage
    if (!savedChats) {
      setSavedChats(chats);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeChat, chats]);

  // Function để xóa session ở backend
  const endChatSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_URL}/end_chat/${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      
      if (!response.ok) {
        console.warn(`Failed to end session ${sessionId} on server:`, response.status);
      } else {
        console.log(`Session ${sessionId} ended successfully`);
      }
    } catch (error) {
      console.error(`Error ending session ${sessionId}:`, error);
    }
  };

  // Cleanup khi component unmount
  useEffect(() => {
    return () => {
      // Cleanup all active sessions when component unmounts
      chats.forEach(chat => {
        if (chat.session_id && !chat.isGuide) {
          endChatSession(chat.session_id);
        }
      });
    };
  }, []);

  // Handle khi user thoát khỏi trang
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      // Cleanup sessions when user closes/refreshes page
      chats.forEach(chat => {
        if (chat.session_id && !chat.isGuide) {
          // Use sendBeacon for reliable cleanup on page unload
          navigator.sendBeacon(`${API_URL}/end_chat/${chat.session_id}`, 
            JSON.stringify({}));
        }
      });
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [chats]);

  const getCurrentChat = () => {
    return chats.find(chat => chat.id === activeChat);
  };

  const updateChatMessages = (chatId, newMessages) => {
    setChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, messages: newMessages }
        : chat
    ));
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const currentChat = getCurrentChat();
    if (!currentChat) {
      console.error("Current chat not found");
      return;
    }

    if (!currentChat.session_id || !currentChat.product_id) {
      alert("Chat này chưa được liên kết với sản phẩm. Vui lòng tạo chat mới với link sản phẩm!");
      return;
    }

    const newMessage = { 
      sender: "user", 
      text: input,
      timestamp: new Date()
    };
    const newMessages = [...currentChat.messages, newMessage];
    updateChatMessages(activeChat, newMessages);
    
    const messageToSend = input;
    setInput("");
    setIsTyping(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageToSend,
          session_id: currentChat.session_id,
          product_id: currentChat.product_id
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("API Response:", data);

      // Parse response correctly
      let botResponse;
      if (typeof data.response === "string") {
        try {
          // Try to parse if it's a JSON string
          const parsedResponse = JSON.parse(data.response);
          botResponse = {
            content: parsedResponse.content || data.response,
            images: parsedResponse.images || []
          };
        } catch {
          // If not JSON, treat as plain string
          botResponse = { content: data.response, images: [] };
        }
      } else if (data.response && typeof data.response === "object") {
        botResponse = {
          content: data.response.content || "Không có phản hồi từ server",
          images: data.response.images || []
        };
      } else {
        botResponse = { content: "Không có phản hồi từ server", images: [] };
      }
      
      setTimeout(() => {
        updateChatMessages(activeChat, [...newMessages, { 
          sender: "bot", 
          text: botResponse.content,
          images: Array.isArray(botResponse.images) ? botResponse.images : [],
          timestamp: new Date()
        }]);
        setIsTyping(false);
      }, 500);
    } catch (error) {
      console.error("Error sending message:", error);
      setTimeout(() => {
        updateChatMessages(activeChat, [...newMessages, { 
          sender: "bot", 
          text: "Xin lỗi, có lỗi xảy ra khi kết nối với server. Vui lòng thử lại sau.",
          timestamp: new Date()
        }]);
        setIsTyping(false);
      }, 500);
    }
  };

  const createNewChat = async () => {
    if (!linkInput.trim()) {
      setError("Vui lòng nhập link!");
      return;
    }

    // Kiểm tra định dạng link cơ bản phía frontend
    if (!linkInput.includes('tiki.vn')) {
      setError("Vui lòng nhập link từ Tiki (tiki.vn)!");
      return;
    }

    setError("");
    setIsCreatingChat(true);

    try {
      const response = await fetch(`${API_URL}/create_chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ link: linkInput }),
      });

      const data = await response.json();
      
      // Xử lý lỗi từ backend
      if (!response.ok) {
        const errorMessage = data.detail || `Lỗi HTTP: ${response.status}`;
        throw new Error(errorMessage);
      }

      console.log("Create Chat Response:", data);
      
      // Kiểm tra dữ liệu trả về
      if (!data.session_id) {
        throw new Error("Server không trả về session_id");
      }
      
      const newChat = {
        id: Date.now(),
        session_id: data.session_id,
        product_id: data.Id || data.id || data.product_id,
        title: data.name_product || `Chat ${chats.length + 1}`,
        messages: [
          { 
            sender: "bot", 
            text: data.name_product 
              ? `Mình đã lấy xong các thông tin và đánh giá về sản phẩm cho bạn:

**Sản phẩm:** ${data.name_product}

Bây giờ bạn có thể hỏi mình về sản phẩm này.` 
              : `Đã tạo chat mới với link: ${linkInput}

Bạn có thể bắt đầu hỏi về sản phẩm ngay bây giờ!`,
            images: Array.isArray(data.img_product) 
              ? data.img_product 
              : (data.img_product ? [data.img_product] : []),
            timestamp: new Date()
          }
        ],
        createdAt: new Date(),
        link: linkInput
      };

      setChats(prev => [...prev, newChat]);
      setActiveChat(newChat.id);
      setShowAddModal(false);
      setLinkInput("");
      setError("");
    } catch (error) {
      console.error("Error creating new chat:", error);
      
      let errorMessage = "Có lỗi không xác định xảy ra";
      
      if (error.message.includes("Không phải link tiki")) {
        errorMessage = "Link không hợp lệ! Vui lòng nhập link sản phẩm từ Tiki.vn";
      } else if (error.message.includes("không chứa sản phẩm")) {
        errorMessage = "Link Tiki không chứa sản phẩm! Vui lòng nhập link sản phẩm cụ thể";
      } else if (error.message.includes("Lỗi server")) {
        errorMessage = error.message;
      } else if (error.message.includes("Failed to fetch")) {
        errorMessage = "Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng";
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsCreatingChat(false);
    }
  };

  // Cập nhật function deleteChat với cleanup backend
  const deleteChat = async (chatId) => {
    const chatToDelete = chats.find(chat => chat.id === chatId);
    
    if (chatToDelete?.isGuide) {
      alert("Không thể xóa chat hướng dẫn!");
      return;
    }
    
    if (chats.length === 1) {
      alert("Không thể xóa chat cuối cùng!");
      return;
    }
    
    // Xóa session ở backend nếu có
    if (chatToDelete?.session_id) {
      await endChatSession(chatToDelete.session_id);
    }
    
    // Xóa chat ở frontend
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    
    // Chuyển sang chat khác nếu đang ở chat bị xóa
    if (activeChat === chatId) {
      const remainingChats = chats.filter(chat => chat.id !== chatId);
      if (remainingChats.length > 0) {
        setActiveChat(remainingChats[0].id);
      }
    }
  };

  // Function xóa tất cả chat (tuỳ chọn)
  const clearAllChats = async () => {
    if (!confirm('Bạn có chắc muốn xóa tất cả chat? Hành động này không thể hoàn tác!')) {
      return;
    }

    const sessionsToEnd = chats
      .filter(chat => chat.session_id && !chat.isGuide)
      .map(chat => chat.session_id);

    // End all sessions concurrently
    await Promise.allSettled(
      sessionsToEnd.map(sessionId => endChatSession(sessionId))
    );

    // Keep only the guide chat
    const guideChat = chats.find(chat => chat.isGuide);
    if (guideChat) {
      setChats([guideChat]);
      setActiveChat(guideChat.id);
    } else {
      // Create new guide chat if not found
      const newGuideChat = {
        id: 1,
        title: "Hướng dẫn sử dụng",
        messages: [
          { 
            sender: "bot", 
            text: `**Chào mừng bạn đến với AI Shopping Assistant!**

Tôi là trợ lý mua sắm thông minh, có thể giúp bạn:

**Các tính năng chính:**
- Tư vấn sản phẩm chi tiết.
- Đánh giá ưu nhược điểm từ các đánh giá của khách hàng đã mua sản phẩm.
- Giúp bạn tổng hợp các phản hồi của khách hàng qua đó giúp bạn biết tình trạng thực tế của sản phẩm mà không cần phải đi đọc từng bình luận.

**Cách sử dụng:**
- 1. Nhấn nút **"Chat mới"** ở sidebar
- 2. Dán link sản phẩm từ các trang thương mại điện tử
- 3. Chờ tôi lấy thông tin sản phẩm
- 4. Bắt đầu hỏi bất cứ điều gì về sản phẩm!

Hãy tạo chat mới với link sản phẩm để bắt đầu nhé!`,
            timestamp: new Date()
          }
        ],
        createdAt: new Date(),
        session_id: null,
        product_id: null,
        isGuide: true
      };
      setChats([newGuideChat]);
      setActiveChat(1);
    }
  };

  const formatTime = (date) => {
    try {
      return date.toLocaleTimeString('vi-VN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch (error) {
      return "00:00";
    }
  };

  const formatDate = (date) => {
    try {
      return date.toLocaleDateString('vi-VN');
    } catch (error) {
      return "N/A";
    }
  };

  const currentChat = getCurrentChat();
  if (!currentChat) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Không tìm thấy chat</h2>
          <p className="text-gray-600">Vui lòng tạo chat mới</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-16'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <h2 className="text-lg font-semibold text-gray-800">Quản lý Chat</h2>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Settings className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="p-4">
          <button
            onClick={() => setShowAddModal(true)}
            className={`${sidebarOpen ? 'w-full' : 'w-full'} bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center justify-center gap-2 py-3 transition-colors`}
          >
            <Plus className="w-5 h-5" />
            {sidebarOpen && <span>Chat mới</span>}
          </button>
          
          {/* Button xóa tất cả chat (chỉ hiện khi có nhiều hơn 1 chat) */}
          {sidebarOpen && chats.filter(chat => !chat.isGuide).length > 0 && (
            <button
              onClick={clearAllChats}
              className="w-full mt-2 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center justify-center gap-2 py-2 transition-colors text-sm"
            >
              <Trash2 className="w-4 h-4" />
              <span>Xóa tất cả</span>
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {chats.map(chat => (
            <div
              key={chat.id}
              className={`mb-2 rounded-lg transition-all cursor-pointer group ${
                activeChat === chat.id 
                  ? 'bg-blue-50 border-blue-200 border' 
                  : 'hover:bg-gray-50 border border-transparent'
              }`}
              onClick={() => setActiveChat(chat.id)}
            >
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <MessageSquare className={`w-5 h-5 flex-shrink-0 ${
                      activeChat === chat.id ? 'text-blue-500' : 'text-gray-400'
                    }`} />
                    {sidebarOpen && (
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm text-gray-800 truncate">
                          {chat.title}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatDate(chat.createdAt)}
                        </p>
                        {!chat.isGuide && (
                          <div className="flex items-center gap-1 mt-1">
                            <div className={`w-2 h-2 rounded-full ${
                              chat.session_id ? 'bg-green-400' : 'bg-gray-400'
                            }`}></div>
                            <p className="text-xs text-gray-400">
                              {chat.session_id ? 'Đã kết nối' : 'Chưa kết nối'}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  {sidebarOpen && !chat.isGuide && (
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        
                        // Hiển thị loading state
                        const button = e.currentTarget;
                        const originalContent = button.innerHTML;
                        button.disabled = true;
                        button.innerHTML = '<div class="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>';
                        
                        try {
                          await deleteChat(chat.id);
                        } catch (error) {
                          console.error('Error deleting chat:', error);
                          alert('Có lỗi xảy ra khi xóa chat!');
                        } finally {
                          // Reset button state (nếu component vẫn còn)
                          if (button && button.parentNode) {
                            button.disabled = false;
                            button.innerHTML = originalContent;
                          }
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded text-red-500 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="flex-1 bg-white/80 backdrop-blur-sm shadow-none border-none flex flex-col overflow-hidden w-full h-full">
          
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 text-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h1 className="text-lg font-semibold">{currentChat.title}</h1>
                <p className="text-sm text-blue-100">
                  {currentChat.isGuide 
                    ? '' 
                    : currentChat.session_id 
                      ? 'Đã kết nối với sản phẩm' 
                      : '⚠️ Chưa kết nối sản phẩm'
                  }
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className={`w-2 h-2 rounded-full animate-pulse ${
                  currentChat.isGuide 
                    ? 'bg-blue-400' 
                    : currentChat.session_id 
                      ? 'bg-green-400' 
                      : 'bg-yellow-400'
                }`}></div>
                {currentChat.isGuide 
                  ? 'Hướng dẫn' 
                  : currentChat.session_id 
                    ? 'Đang hoạt động' 
                    : 'Chế độ cơ bản'
                }
              </div>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
            {currentChat.messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex items-start gap-3 ${
                  msg.sender === "user" ? "flex-row-reverse" : ""
                }`}
                style={{
                  animation: 'fadeIn 0.3s ease-out'
                }}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.sender === "user" 
                    ? "bg-blue-500 text-white" 
                    : "bg-gradient-to-br from-purple-500 to-pink-500 text-white"
                }`}>
                  {msg.sender === "user" ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                </div>

                <div className={`max-w-[70%] ${msg.sender === "user" ? "text-right" : ""}`}>
                  <div className={`rounded-2xl px-4 py-3 shadow-sm ${
                    msg.sender === "user"
                      ? "bg-blue-500 text-white rounded-tr-sm"
                      : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
                  }`}>
                    {msg.text && (
                        <div className="text-sm leading-relaxed mb-2">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.text}
                          </ReactMarkdown>
                        </div>
                      )}
                    {Array.isArray(msg.images) && msg.images.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {msg.images.map((img, index) => (
                          <img
                            key={index}
                            src={img}
                            alt={`Ảnh sản phẩm ${index + 1}`}
                            className="rounded-lg max-w-xs border hover:scale-105 transition-transform cursor-pointer"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              console.error("Error loading image:", img);
                            }}
                            onClick={() => window.open(img, '_blank')}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                  <p className={`text-xs text-gray-500 mt-1 ${
                    msg.sender === "user" ? "text-right" : "text-left"
                  }`}>
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex items-start gap-3" style={{ animation: 'fadeIn 0.3s ease-out' }}>
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-white border-t border-gray-200">
            {!currentChat.session_id && !currentChat.isGuide && (
              <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                Chat này chưa được liên kết với sản phẩm. Vui lòng tạo chat mới với link sản phẩm để sử dụng AI Assistant.
                </p>
              </div>
            )}
            
            {currentChat.isGuide && (
              <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                Đây là chat hướng dẫn. Hãy tạo chat mới với link sản phẩm để bắt đầu tư vấn!
                </p>
              </div>
            )}
            
            <div className="flex items-center gap-3">
              <div className="flex-1 relative">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                  className="w-full px-4 py-3 bg-gray-100 rounded-full border-0 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all duration-200 placeholder:text-gray-500"
                  placeholder={
                    currentChat.isGuide
                      ? "Tạo chat mới để bắt đầu tư vấn sản phẩm..."
                      : currentChat.session_id 
                        ? "Nhập câu hỏi về sản phẩm..." 
                        : "Tạo chat mới với link sản phẩm để bắt đầu chat..."
                  }
                  disabled={isTyping || !currentChat.session_id || currentChat.isGuide}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isTyping || !currentChat.session_id || currentChat.isGuide}
                className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full flex items-center justify-center hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex items-center justify-center mt-3">
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                AI có thể mắc lỗi. Hãy kiểm tra thông tin quan trọng.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Add Chat Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {isCreatingChat ? "Đang tạo chat..." : "Tạo Chat Mới"}
              </h3>
              {!isCreatingChat && (
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setError("");
                    setLinkInput("");
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
            
            {isCreatingChat ? (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <h4 className="text-lg font-medium text-gray-800 mb-2">Đang lấy thông tin sản phẩm...</h4>
                <p className="text-sm text-gray-600">
                  Vui lòng đợi trong giây lát, tôi đang thu thập thông tin sản phẩm để tư vấn tốt nhất cho bạn.
                </p>
                <div className="mt-4 flex items-center justify-center gap-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            ) : (
              <>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nhập link sản phẩm:
                  </label>
                  <input
                    type="url"
                    value={linkInput}
                    onChange={(e) => {
                      setLinkInput(e.target.value);
                      setError("");
                    }}
                    placeholder="https://tiki.vn/..."
                    className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                      error ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                  />
                  
                  {/* Hiển thị lỗi */}
                  {error && (
                    <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-700 flex items-center gap-2">
                        <span className="text-red-500">❌</span>
                        {error}
                      </p>
                    </div>
                  )}
                  
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-blue-700 mb-2">
                      <strong>Lưu ý:</strong> Mình chỉ mới hỗ trợ sản phẩm từ Tiki
                    </p>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowAddModal(false);
                      setError("");
                      setLinkInput("");
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Hủy
                  </button>
                  <button
                    onClick={createNewChat}
                    disabled={!linkInput.trim() || error}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Tạo Chat
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

export default App;