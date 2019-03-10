package id.nerdstudio.footballapps

import android.content.Intent
import android.os.Bundle
import android.support.v4.app.Fragment
import android.support.v7.app.AppCompatActivity
import android.support.v7.widget.SearchView
import android.view.Menu
import id.nerdstudio.footballapps.R.id.*
import id.nerdstudio.footballapps.favorites.fragment.FavoriteMatchListFragment
import id.nerdstudio.footballapps.favorites.fragment.FavoriteTeamListFragment
import id.nerdstudio.footballapps.favorites.fragment.FavoritesFragment
import id.nerdstudio.footballapps.matches.fragment.MatchesFragment
import id.nerdstudio.footballapps.teams.fragment.TeamsFragment
import kotlinx.android.synthetic.main.activity_main.*
import org.jetbrains.anko.dip

class AndroidActivity : AppCompatActivity() {
    lateinit var currentFragment: Fragment

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        supportActionBar?.elevation = dip(0).toFloat()

        bottom_navigation.setOnNavigationItemSelectedListener { item ->
            when (item.itemId) {
                matches -> {
                    currentFragment = MatchesFragment()
                }
                teams -> {
                    currentFragment = TeamsFragment()
                    replaceFragment(savedInstanceState, TeamsFragment())
                }
                favorites -> {
                    currentFragment = FavoritesFragment()
                    replaceFragment(savedInstanceState, FavoritesFragment())
                }
            }
            replaceFragment(savedInstanceState, currentFragment)
            true
        }
        bottom_navigation.selectedItemId = matches
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 100 && resultCode == RESULT_OK) {
            if (currentFragment is FavoritesFragment) {
                val fragment = (currentFragment as FavoritesFragment).mPagerAdapter.getItem((currentFragment as FavoritesFragment).root.mViewPager.currentItem)
                if (fragment is FavoriteTeamListFragment) {
                    fragment.loadData()
                } else if (fragment is FavoriteMatchListFragment) {
                    fragment.loadData()
                }
            }
        }
    }

    override fun onPrepareOptionsMenu(menu: Menu): Boolean {
        val search = menu.findItem(R.id.action_search)
        search.isVisible = (currentFragment != FavoritesFragment())
        return true
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        val inflater = menuInflater
        inflater.inflate(R.menu.menu_search, menu)

        val mSearch = menu.findItem(R.id.action_search)
        val mSearchView = mSearch.actionView as SearchView
        mSearchView.queryHint = getString(R.string.search)
        mSearchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String): Boolean {
                return false
            }

            override fun onQueryTextChange(query: String): Boolean {
                when (currentFragment) {
                    is MatchesFragment -> {
                        (currentFragment as MatchesFragment).search(query)
                    }
                    is TeamsFragment -> {
                        (currentFragment as TeamsFragment).search(query)
                    }
                }
                return false
            }
        })

        return super.onCreateOptionsMenu(menu)
    }

    private fun replaceFragment(savedInstanceState: Bundle?, fragment: Fragment) {
        if (savedInstanceState == null) {
            supportFragmentManager
                    .beginTransaction()
                    .replace(R.id.main_container, fragment, fragment::class.java.simpleName)
                    .commit()
        }
    }
}