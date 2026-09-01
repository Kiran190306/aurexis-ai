package com.jarvis.ai

import android.app.Application
import com.jarvis.ai.data.api.ApiClient
import com.jarvis.ai.data.repository.AuthRepository
import com.jarvis.ai.data.repository.ConversationRepository
import com.jarvis.ai.data.store.TokenStore

class JarvisApplication : Application() {
    
    lateinit var apiClient: ApiClient
    lateinit var tokenStore: TokenStore
    lateinit var authRepository: AuthRepository
    lateinit var conversationRepository: ConversationRepository
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize dependencies
        tokenStore = TokenStore(this)
        apiClient = ApiClient(tokenStore)
        authRepository = AuthRepository(apiClient, tokenStore)
        conversationRepository = ConversationRepository(apiClient)
    }
    
    companion object {
        lateinit var instance: JarvisApplication
            private set
    }
    
    init {
        instance = this
    }
}
